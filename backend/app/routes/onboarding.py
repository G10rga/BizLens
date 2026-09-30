from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Business, FixedExpense, SupplierPayment
from .helpers import current_user

bp = Blueprint("onboarding", __name__, url_prefix="/api/onboarding")

VALID_TYPES = {"bakery", "restaurant", "retail", "pharmacy", "salon", "other"}
VALID_CITIES = {"Tbilisi", "Batumi", "Kutaisi", "Other"}


@bp.post("/profile")
@jwt_required()
def save_profile():
    user = current_user()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    business_type = (data.get("business_type") or "other").strip().lower()
    city = data.get("city") or "Tbilisi"

    if not name:
        return jsonify({"error": "Business name is required"}), 400
    if business_type not in VALID_TYPES:
        return jsonify({"error": f"business_type must be one of {sorted(VALID_TYPES)}"}), 400
    if city not in VALID_CITIES:
        city = "Other"

    business = user.business
    if business is None:
        business = Business(owner_id=user.id, name=name, business_type=business_type, city=city)
        db.session.add(business)
    else:
        business.name = name
        business.business_type = business_type
        business.city = city
    db.session.commit()
    return jsonify(business.to_dict())


@bp.post("/expenses")
@jwt_required()
def save_expenses():
    user = current_user()
    if not user.business:
        return jsonify({"error": "Create business profile first"}), 400
    data = request.get_json(silent=True) or {}
    items = data.get("expenses") or []

    FixedExpense.query.filter_by(business_id=user.business.id).delete()
    for item in items:
        name = (item.get("name") or "").strip()
        amount = float(item.get("amount") or 0)
        due_day = int(item.get("due_day") or 1)
        if not name or amount <= 0:
            continue
        due_day = min(max(due_day, 1), 28)
        db.session.add(
            FixedExpense(
                business_id=user.business.id,
                name=name,
                amount=amount,
                due_day=due_day,
            )
        )
    db.session.commit()
    expenses = FixedExpense.query.filter_by(business_id=user.business.id).all()
    return jsonify([e.to_dict() for e in expenses])


@bp.post("/suppliers")
@jwt_required()
def save_suppliers():
    user = current_user()
    if not user.business:
        return jsonify({"error": "Create business profile first"}), 400
    data = request.get_json(silent=True) or {}
    items = data.get("suppliers") or []
    skip = bool(data.get("skip"))

    SupplierPayment.query.filter_by(business_id=user.business.id).delete()
    if not skip:
        for item in items:
            name = (item.get("name") or "").strip() or "Supplier"
            amount = float(item.get("amount") or 0)
            every_n_days = int(item.get("every_n_days") or 14)
            next_due = item.get("next_due_date") or date.today().isoformat()
            if amount <= 0:
                continue
            db.session.add(
                SupplierPayment(
                    business_id=user.business.id,
                    name=name,
                    amount=amount,
                    every_n_days=max(1, every_n_days),
                    next_due_date=date.fromisoformat(next_due),
                )
            )
    db.session.commit()
    suppliers = SupplierPayment.query.filter_by(business_id=user.business.id).all()
    return jsonify([s.to_dict() for s in suppliers])


@bp.post("/cash")
@jwt_required()
def save_cash():
    user = current_user()
    if not user.business:
        return jsonify({"error": "Create business profile first"}), 400
    data = request.get_json(silent=True) or {}
    cash = float(data.get("cash_on_hand") or 0)
    user.business.cash_on_hand = cash
    user.business.cash_baseline_date = date.today()
    user.business.onboarding_complete = True
    db.session.commit()
    return jsonify(user.business.to_dict())


@bp.get("/status")
@jwt_required()
def status():
    user = current_user()
    business = user.business
    if not business:
        return jsonify({"step": "profile", "complete": False})
    has_expenses = FixedExpense.query.filter_by(business_id=business.id).count() > 0
    if not has_expenses and not business.onboarding_complete:
        return jsonify({"step": "expenses", "complete": False, "business": business.to_dict()})
    if not business.onboarding_complete:
        return jsonify({"step": "cash", "complete": False, "business": business.to_dict()})
    return jsonify({"step": "done", "complete": True, "business": business.to_dict()})
