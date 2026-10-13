from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Business, FixedExpense, SupplierPayment
from ..validation import parse_money, validate_business_name, validate_due_day
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
    business_type = (data.get("business_type") or "").strip().lower()
    city = (data.get("city") or "").strip()

    name_err = validate_business_name(name)
    if name_err:
        return jsonify({"error": name_err}), 400
    if business_type not in VALID_TYPES:
        return jsonify({"error": "Select a business type"}), 400
    if city not in VALID_CITIES:
        return jsonify({"error": "Select a city"}), 400

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
        try:
            amount = parse_money(item.get("amount"), min_value=0)
            due_day = validate_due_day(item.get("due_day") or 1)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if not name or amount <= 0:
            continue
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
            name = (item.get("name") or "").strip()
            amount_raw = item.get("amount")
            n_raw = item.get("every_n_days")
            any_filled = bool(name or str(amount_raw or "").strip() or str(n_raw or "").strip())
            if not any_filled:
                continue
            if not 2 <= len(name) <= 80:
                return jsonify({"error": "Supplier name must be 2–80 characters"}), 400
            try:
                amount = parse_money(amount_raw, min_value=0.01)
                every_n_days = int(n_raw)
            except (TypeError, ValueError):
                return jsonify({"error": "Supplier amount and schedule are required"}), 400
            if not 1 <= every_n_days <= 365:
                return jsonify({"error": "Every N days must be a whole number from 1 to 365"}), 400
            next_due = item.get("next_due_date") or date.today().isoformat()
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
    try:
        cash = parse_money(data.get("cash_on_hand"), min_value=0)
    except ValueError:
        return jsonify({"error": "Cash on hand must be 0 or more, with up to 2 decimals"}), 400
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
