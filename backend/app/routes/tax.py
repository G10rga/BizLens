"""Tax summary and obligations API."""

from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..models import FixedExpense, SupplierPayment
from ..services.cashflow import expand_fixed_expenses, expand_supplier_payments, merge_expense_maps
from ..services.georgian_tax import (
    estimate_period,
    profile_from_business,
    resolve_obligations,
    rolling_12m_turnover,
    ytd_turnover,
)
from ..services.sales_agg import daily_rows_for_business
from .helpers import require_business

bp = Blueprint("tax", __name__, url_prefix="/api/tax")


def _period_bounds(period: str, as_of: date):
    period = (period or "ytd").lower()
    if period == "month":
        start = date(as_of.year, as_of.month, 1)
        end = as_of
    else:
        start = date(as_of.year, 1, 1)
        end = as_of
    return start, end


def _sum_revenue(rows, start: date, end: date) -> float:
    total = 0.0
    for row in rows:
        d = date.fromisoformat(row["date"])
        if start <= d <= end:
            total += float(row["revenue"] or 0)
    return round(total, 2)


def _sum_expenses(expenses, suppliers, start: date, end: date) -> tuple[float, float]:
    merged = merge_expense_maps(
        expand_fixed_expenses(expenses, start, end),
        expand_supplier_payments(suppliers, start, end),
    )
    total = 0.0
    salary = 0.0
    for items in merged.values():
        for item in items:
            amt = float(item.get("amount") or 0)
            total += amt
            if (item.get("name") or "").lower() == "salaries":
                salary += amt
    return round(total, 2), round(salary, 2)


@bp.get("/summary")
@jwt_required()
@require_business
def tax_summary(business):
    period = request.args.get("period") or "ytd"
    as_of = date.today()
    start, end = _period_bounds(period, as_of)
    rows = daily_rows_for_business(business.id)
    expenses = [e.to_dict() for e in FixedExpense.query.filter_by(business_id=business.id).all()]
    suppliers = [s.to_dict() for s in SupplierPayment.query.filter_by(business_id=business.id).all()]

    income = _sum_revenue(rows, start, end)
    expense_total, salary_total = _sum_expenses(expenses, suppliers, start, end)
    profile = profile_from_business(business)

    summary = estimate_period(
        profile=profile,
        income_total=income,
        expense_total=expense_total,
        salary_expense_total=salary_total,
        tax_reserve=float(business.tax_reserve or 0),
        vat_reserve=float(business.vat_reserve or 0),
        cash_on_hand=float(business.cash_on_hand or 0),
        ytd_turnover_value=ytd_turnover(rows, as_of),
        rolling_12m=rolling_12m_turnover(rows, as_of),
    )
    summary["period"] = period
    summary["period_start"] = start.isoformat()
    summary["period_end"] = end.isoformat()
    summary["tax_profile_complete"] = bool(business.tax_profile_complete)
    summary["profile"] = {
        "legal_form": business.legal_form,
        "tax_regime": business.tax_regime,
        "is_vat_payer": bool(business.is_vat_payer),
        "has_employees": bool(business.has_employees),
        "pension_participants": bool(business.pension_participants),
        "llc_distributes_profit": bool(business.llc_distributes_profit),
    }
    return jsonify(summary)


@bp.get("/obligations")
@jwt_required()
@require_business
def tax_obligations(business):
    if not business.tax_profile_complete:
        return jsonify({"obligations": [], "tax_profile_complete": False})
    return jsonify(
        {
            "obligations": resolve_obligations(profile_from_business(business)),
            "tax_profile_complete": True,
        }
    )
