from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from .helpers import current_user, require_business

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("")
@jwt_required()
def get_settings():
    user = current_user()
    payload = {"user": user.to_dict()}
    if user.business:
        payload["business"] = user.business.to_dict()
    return jsonify(payload)


@bp.put("")
@jwt_required()
def update_settings():
    user = current_user()
    data = request.get_json(silent=True) or {}

    if "language" in data and data["language"] in {"ka", "en"}:
        user.language = data["language"]
    if "full_name" in data:
        user.full_name = (data.get("full_name") or "").strip() or None

    if user.business and "business" in data:
        b = data["business"] or {}
        if "name" in b:
            user.business.name = (b.get("name") or user.business.name).strip()
        if "business_type" in b and b["business_type"]:
            user.business.business_type = b["business_type"]
        if "city" in b and b["city"]:
            user.business.city = b["city"]

    db.session.commit()
    payload = {"user": user.to_dict()}
    if user.business:
        payload["business"] = user.business.to_dict()
    return jsonify(payload)


@bp.get("/business")
@jwt_required()
@require_business
def get_business(business):
    return jsonify(business.to_dict())
