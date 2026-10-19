from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..config import Config
from ..extensions import db
from ..models import Alert, FixedExpense, SupplierPayment
from ..services.alerts import build_alerts
from ..services.cashflow import (
    expand_fixed_expenses,
    expand_supplier_payments,
    merge_expense_maps,
    project_cashflow,
)
from ..services.forecast import backtest_forecast, forecast_sales
from ..services.georgian_tax import (
    estimate_period,
    expand_tax_payments,
    profile_from_business,
    rolling_12m_turnover,
    ytd_turnover,
)
from ..services.lens_completeness import completeness_report, recent_capture_widen_factor
from ..services.sales_agg import daily_rows_for_business
from .helpers import require_business

bp = Blueprint("forecast", __name__, url_prefix="/api/forecast")


def run_business_forecast(business, horizon_days=None):
    horizon = int(horizon_days or Config.FORECAST_HORIZON_DAYS)
    horizon = max(7, min(horizon, 180))
    daily = daily_rows_for_business(business.id)
    # Forecast from the last day we actually have sales for.
    # So if you drop September for a holdout test, prediction starts Sep 1 — not "today".
    if daily:
        last_hist = max(date.fromisoformat(r["date"]) for r in daily)
        as_of = last_hist
    else:
        as_of = date.today()
    forecast = forecast_sales(
        daily,
        business_type=business.business_type,
        horizon_days=horizon,
        as_of=as_of,
    )
    expenses = [e.to_dict() for e in FixedExpense.query.filter_by(business_id=business.id).all()]
    suppliers = [s.to_dict() for s in SupplierPayment.query.filter_by(business_id=business.id).all()]
    start_date = as_of + timedelta(days=1)
    end_date = start_date + timedelta(days=horizon - 1)
    tax_payments = None
    if getattr(business, "tax_profile_complete", False):
        tax_payments = expand_tax_payments(
            profile=profile_from_business(business),
            daily_rows=daily,
            expenses=expenses,
            start=start_date,
            end=end_date,
            # Future months have no DailySale rows — use forecast so tax due
            # dates (15th) still hit the cash timeline.
            income_forecast=forecast.get("income_forecast") or [],
        )
    # Incomplete Lens capture → wider forecast ranges on the dashboard cards
    widen = recent_capture_widen_factor(business, lookback_days=7)
    cashflow = project_cashflow(
        starting_cash=float(business.cash_on_hand),
        start_date=start_date,
        horizon_days=horizon,
        income_series=forecast["income_forecast"],
        expenses=expenses,
        suppliers=suppliers,
        range_widen_factor=widen,
        tax_payments=tax_payments,
        tax_reserve=float(getattr(business, "tax_reserve", 0) or 0),
        vat_reserve=float(getattr(business, "vat_reserve", 0) or 0),
    )
    return forecast, cashflow, as_of


def regenerate_alerts(business):
    _, cashflow, _ = run_business_forecast(business)
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
    chart_horizon = request.args.get("horizon", type=int) or Config.FORECAST_HORIZON_DAYS
    chart_horizon = max(7, min(chart_horizon, 180))
    # Always compute 90 days so 30/60/90 sales cards stay correct
    forecast, cashflow, as_of = run_business_forecast(business, horizon_days=90)
    timeline = cashflow["timeline"]
    daily = daily_rows_for_business(business.id)
    tax_summary = None
    if getattr(business, "tax_profile_complete", False):
        year_start = date(as_of.year, 1, 1)
        income_ytd = sum(
            float(r["revenue"] or 0)
            for r in daily
            if year_start <= date.fromisoformat(r["date"]) <= as_of
        )
        expenses = [e.to_dict() for e in FixedExpense.query.filter_by(business_id=business.id).all()]
        suppliers = [s.to_dict() for s in SupplierPayment.query.filter_by(business_id=business.id).all()]

        merged = merge_expense_maps(
            expand_fixed_expenses(expenses, year_start, as_of),
            expand_supplier_payments(suppliers, year_start, as_of),
        )
        expense_ytd = 0.0
        salary_ytd = 0.0
        for items in merged.values():
            for item in items:
                amt = float(item.get("amount") or 0)
                expense_ytd += amt
                if (item.get("name") or "").lower() == "salaries":
                    salary_ytd += amt
        tax_summary = estimate_period(
            profile=profile_from_business(business),
            income_total=income_ytd,
            expense_total=expense_ytd,
            salary_expense_total=salary_ytd,
            tax_reserve=float(business.tax_reserve or 0),
            vat_reserve=float(business.vat_reserve or 0),
            cash_on_hand=float(business.cash_on_hand or 0),
            ytd_turnover_value=ytd_turnover(daily, as_of),
            rolling_12m=rolling_12m_turnover(daily, as_of),
        )
    return jsonify(
        {
            "business": business.to_dict(),
            "model": forecast["model"],
            "history_days": forecast["history_days"],
            "horizon_days": 90,
            "chart_horizon": chart_horizon,
            "as_of": as_of.isoformat(),
            "forecast_starts": (as_of + timedelta(days=1)).isoformat(),
            "baseline_daily": forecast.get("baseline_daily"),
            "recent_avg_raw": forecast.get("recent_avg_raw"),
            "calibration_scale": forecast.get("calibration_scale"),
            "backtest": forecast.get("backtest"),
            "history": forecast["history"],
            "income_forecast": forecast["income_forecast"][:chart_horizon],
            "holiday_markers": forecast["holiday_markers"],
            "timeline": timeline[:chart_horizon],
            "timeline_full": timeline,
            "expense_markers": [
                m for m in cashflow["expense_markers"]
                if timeline and m["date"] <= timeline[min(len(timeline), chart_horizon) - 1]["date"]
            ] if timeline else cashflow["expense_markers"],
            "summary": cashflow["summary"],
            "tax_summary": tax_summary,
            "lens_completeness": completeness_report(business, days=14),
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


@bp.get("/backtest")
@jwt_required()
@require_business
def backtest(business):
    holdout = request.args.get("holdout", default=30, type=int)
    holdout = max(7, min(holdout, 60))
    daily = daily_rows_for_business(business.id)
    result = backtest_forecast(
        daily,
        business_type=business.business_type,
        holdout_days=holdout,
    )
    status = 400 if result.get("error") else 200
    return jsonify(result), status
