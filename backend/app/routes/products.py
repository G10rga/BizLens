from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Product
from .helpers import require_business

bp = Blueprint("products", __name__, url_prefix="/api/products")


def _normalize_barcode(raw) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _barcode_taken(business_id: int, barcode: str | None, exclude_id: int | None = None) -> bool:
    if not barcode:
        return False
    q = Product.query.filter_by(business_id=business_id, barcode=barcode)
    if exclude_id is not None:
        q = q.filter(Product.id != exclude_id)
    return q.first() is not None


@bp.get("")
@jwt_required()
@require_business
def list_products(business):
    active_only = request.args.get("active", "true").lower() != "false"
    q = Product.query.filter_by(business_id=business.id)
    if active_only:
        q = q.filter_by(active=True)
    products = q.order_by(Product.name.asc()).all()
    return jsonify([p.to_dict() for p in products])


@bp.post("")
@jwt_required()
@require_business
def create_product(business):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    price = float(data.get("price") or 0)
    category = (data.get("category") or "").strip() or None
    barcode = _normalize_barcode(data.get("barcode"))
    if not name or price < 0:
        return jsonify({"error": "name and non-negative price required"}), 400
    if _barcode_taken(business.id, barcode):
        return jsonify({"error": "Barcode already used by another product"}), 400
    product = Product(
        business_id=business.id,
        name=name,
        price=price,
        category=category,
        barcode=barcode,
        active=True,
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@bp.put("/<int:product_id>")
@jwt_required()
@require_business
def update_product(business, product_id):
    product = Product.query.filter_by(id=product_id, business_id=business.id).first_or_404()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        product.name = (data.get("name") or product.name).strip()
    if "price" in data:
        product.price = float(data["price"])
    if "category" in data:
        product.category = (data.get("category") or "").strip() or None
    if "barcode" in data:
        barcode = _normalize_barcode(data.get("barcode"))
        if _barcode_taken(business.id, barcode, exclude_id=product.id):
            return jsonify({"error": "Barcode already used by another product"}), 400
        product.barcode = barcode
    if "active" in data:
        product.active = bool(data["active"])
    db.session.commit()
    return jsonify(product.to_dict())


@bp.delete("/<int:product_id>")
@jwt_required()
@require_business
def delete_product(business, product_id):
    product = Product.query.filter_by(id=product_id, business_id=business.id).first_or_404()
    product.active = False
    db.session.commit()
    return jsonify({"ok": True})
