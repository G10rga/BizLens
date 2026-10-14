from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Product, User
from .helpers import require_business

bp = Blueprint("products", __name__, url_prefix="/api/products")

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


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


def _product_image_dir(business_id: int) -> Path:
    root = Path(current_app.config["UPLOAD_DIR"]) / "products" / str(business_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _delete_image_file(path: str | None) -> None:
    if not path:
        return
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
    except OSError:
        pass


def _save_product_image(business_id: int, product_id: int, file_storage) -> str:
    filename = secure_filename(file_storage.filename or "") or "image.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError("Image must be JPG, PNG, WEBP, or GIF")
    dest = _product_image_dir(business_id) / f"{product_id}{ext}"
    # Remove previous files with other extensions for this product
    for old in _product_image_dir(business_id).glob(f"{product_id}.*"):
        if old != dest:
            try:
                old.unlink()
            except OSError:
                pass
    file_storage.save(dest)
    return str(dest)


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
    if data.get("clear_image"):
        _delete_image_file(product.image_path)
        product.image_path = None
    db.session.commit()
    return jsonify(product.to_dict())


@bp.post("/<int:product_id>/image")
@jwt_required()
@require_business
def upload_product_image(business, product_id):
    product = Product.query.filter_by(id=product_id, business_id=business.id).first_or_404()
    file = request.files.get("image") or request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Image file required"}), 400
    try:
        saved = _save_product_image(business.id, product.id, file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    _delete_image_file(product.image_path if product.image_path != saved else None)
    product.image_path = saved
    db.session.commit()
    return jsonify(product.to_dict())


@bp.get("/<int:product_id>/image")
@jwt_required(locations=["headers", "query_string"])
def get_product_image(product_id):
    # Query-string JWT is used by <img src>; avoid require_business (header-only verify).
    user = db.session.get(User, int(get_jwt_identity()))
    business = user.business if user else None
    if not business:
        return jsonify({"error": "Complete onboarding first"}), 400
    product = Product.query.filter_by(id=product_id, business_id=business.id).first_or_404()
    if not product.image_path or not Path(product.image_path).is_file():
        return jsonify({"error": "Image not found"}), 404
    return send_file(product.image_path)


@bp.delete("/<int:product_id>")
@jwt_required()
@require_business
def delete_product(business, product_id):
    product = Product.query.filter_by(id=product_id, business_id=business.id).first_or_404()
    product.active = False
    db.session.commit()
    return jsonify({"ok": True})
