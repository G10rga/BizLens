from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import FixedExpense, SupplierPayment
from .helpers import require_business

bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


def _expense_payload(business):
    expenses = FixedExpense.query.filter_by(business_id=business.id).all()
    suppliers = SupplierPayment.query.filter_by(business_id=business.id).all()
    return {
        "cash_on_hand": business.cash_on_hand,
        "expenses": [e.to_dict() for e in expenses],
        "suppliers": [s.to_dict() for s in suppliers],
    }


@bp.get("")
@jwt_required()
@require_business
def get_expenses(business):
    return jsonify(_expense_payload(business))


@bp.put("")
@jwt_required()
@require_business
def update_expenses(business):
    data = request.get_json(silent=True) or {}

    if "cash_on_hand" in data:
        business.cash_on_hand = float(data["cash_on_hand"])
        business.cash_baseline_date = date.today()

    if "expenses" in data:
        FixedExpense.query.filter_by(business_id=business.id).delete()
        for item in data["expenses"] or []:
            name = (item.get("name") or "").strip()
            amount = float(item.get("amount") or 0)
            due_day = min(max(int(item.get("due_day") or 1), 1), 28)
            if name and amount > 0:
                db.session.add(
                    FixedExpense(
                        business_id=business.id,
                        name=name,
                        amount=amount,
                        due_day=due_day,
                    )
                )

    if "suppliers" in data:
        SupplierPayment.query.filter_by(business_id=business.id).delete()
        for item in data["suppliers"] or []:
            name = (item.get("name") or "").strip() or "Supplier"
            amount = float(item.get("amount") or 0)
            every_n_days = max(1, int(item.get("every_n_days") or 14))
            next_due = item.get("next_due_date") or date.today().isoformat()
            if amount > 0:
                db.session.add(
                    SupplierPayment(
                        business_id=business.id,
                        name=name,
                        amount=amount,
                        every_n_days=every_n_days,
                        next_due_date=date.fromisoformat(next_due),
                    )
                )

    db.session.commit()
    return jsonify(_expense_payload(business))
