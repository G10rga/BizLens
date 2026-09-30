from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Product
from .helpers import require_business

bp = Blueprint("products", __name__, url_prefix="/api/products")


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
    if not name or price < 0:
        return jsonify({"error": "name and non-negative price required"}), 400
    product = Product(
        business_id=business.id, name=name, price=price, category=category, active=True
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
