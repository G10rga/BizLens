from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Product, Sale, SaleItem
from ..services.sales_agg import today_sales_summary, upsert_daily_revenue
from .helpers import require_business

bp = Blueprint("sales", __name__, url_prefix="/api/sales")


@bp.post("")
@jwt_required()
@require_business
def create_sale(business):
    data = request.get_json(silent=True) or {}
    payment_method = (data.get("payment_method") or "").strip().lower()
    items = data.get("items") or []
    if payment_method not in {"cash", "card"}:
        return jsonify({"error": "payment_method must be cash or card"}), 400
    if not items:
        return jsonify({"error": "Cart is empty"}), 400

    sale_items = []
    total = 0.0
    for raw in items:
        product_id = raw.get("product_id")
        qty = int(raw.get("quantity") or 1)
        if qty <= 0:
            continue
        product = None
        if product_id:
            product = Product.query.filter_by(
                id=product_id, business_id=business.id, active=True
            ).first()
        name = (raw.get("product_name") or (product.name if product else "")).strip()
        unit_price = float(raw.get("unit_price") if raw.get("unit_price") is not None else (product.price if product else 0))
        if not name:
            return jsonify({"error": "Each item needs a product name or product_id"}), 400
        line_total = round(unit_price * qty, 2)
        total += line_total
        sale_items.append(
            {
                "product_id": product.id if product else None,
                "product_name": name,
                "unit_price": unit_price,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    if not sale_items:
        return jsonify({"error": "No valid items"}), 400

    sale = Sale(
        business_id=business.id,
        total=round(total, 2),
        payment_method=payment_method,
        sold_at=datetime.utcnow(),
        source="pos",
    )
    db.session.add(sale)
    db.session.flush()
    for item in sale_items:
        db.session.add(SaleItem(sale_id=sale.id, **item))

    upsert_daily_revenue(business.id, date.today(), sale.total, source="pos")
    # Keep cash_on_hand roughly in sync for cash payments (demo-friendly)
    if payment_method == "cash":
        business.cash_on_hand = float(business.cash_on_hand) + sale.total

    db.session.commit()
    return jsonify(sale.to_dict()), 201


@bp.get("/today")
@jwt_required()
@require_business
def sales_today(business):
    day = request.args.get("date")
    d = date.fromisoformat(day) if day else date.today()
    return jsonify(today_sales_summary(business.id, d))
