from datetime import date, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..config import Config
from ..extensions import db
from ..models import Alert, FixedExpense, SupplierPayment
from ..services.alerts import build_alerts
from ..services.cashflow import project_cashflow
from ..services.forecast import forecast_sales
from ..services.sales_agg import daily_rows_for_business
from .helpers import require_business

bp = Blueprint("forecast", __name__, url_prefix="/api/forecast")


def run_business_forecast(business):
    daily = daily_rows_for_business(business.id)
    forecast = forecast_sales(
        daily,
        business_type=business.business_type,
        horizon_days=Config.FORECAST_HORIZON_DAYS,
        as_of=date.today(),
    )
    expenses = [e.to_dict() for e in FixedExpense.query.filter_by(business_id=business.id).all()]
    suppliers = [s.to_dict() for s in SupplierPayment.query.filter_by(business_id=business.id).all()]
    cashflow = project_cashflow(
        starting_cash=float(business.cash_on_hand),
        start_date=date.today() + timedelta(days=1),
        horizon_days=Config.FORECAST_HORIZON_DAYS,
        income_series=forecast["income_forecast"],
        expenses=expenses,
        suppliers=suppliers,
    )
    return forecast, cashflow


def regenerate_alerts(business):
    _, cashflow = run_business_forecast(business)
    generated = build_alerts(
        business_type=business.business_type,
        cashflow_timeline=cashflow["timeline"],
        expense_markers=cashflow["expense_markers"],
        as_of=date.today(),
    )
    Alert.query.filter_by(business_id=business.id, acknowledged=False).delete()
    saved = []
    for item in generated:
        alert = Alert(
            business_id=business.id,
            severity=item["severity"],
            title=item["title"],
            title_ka=item.get("title_ka"),
            message=item["message"],
            message_ka=item.get("message_ka"),
            alert_date=item.get("alert_date"),
            amount=item.get("amount"),
        )
        db.session.add(alert)
        saved.append(alert)
    db.session.commit()
    return saved


@bp.get("/dashboard")
@jwt_required()
@require_business
def dashboard(business):
    forecast, cashflow = run_business_forecast(business)
    return jsonify(
        {
            "business": business.to_dict(),
            "model": forecast["model"],
            "history_days": forecast["history_days"],
            "history": forecast["history"],
            "income_forecast": forecast["income_forecast"],
            "holiday_markers": forecast["holiday_markers"],
            "timeline": cashflow["timeline"],
            "expense_markers": cashflow["expense_markers"],
            "summary": cashflow["summary"],
            "thresholds": {
                "green": Config.CASH_GREEN_THRESHOLD,
                "yellow": Config.CASH_YELLOW_THRESHOLD,
            },
        }
    )


@bp.post("/refresh-alerts")
@jwt_required()
@require_business
def refresh_alerts(business):
    saved = regenerate_alerts(business)
    return jsonify([a.to_dict() for a in saved])
