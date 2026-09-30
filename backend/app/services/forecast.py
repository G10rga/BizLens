"""Sales forecasting with Facebook Prophet + Georgian Intelligence Layer."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd

from .georgian_calendar import (
    daily_seasonality_factor,
    holiday_markers,
    prophet_holiday_frame,
)


def _prepare_history(daily_rows: List[dict]) -> pd.DataFrame:
    if not daily_rows:
        return pd.DataFrame(columns=["ds", "y", "geo_factor"])

    df = pd.DataFrame(daily_rows)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["revenue"].astype(float)
    df = df.sort_values("ds").drop_duplicates("ds", keep="last")
    return df[["ds", "y"]]


def _fallback_forecast(
    history: pd.DataFrame, horizon: int, business_type: str, start: date
) -> List[dict]:
    """Simple seasonal baseline if Prophet is unavailable or data is thin."""
    if history.empty:
        base = 100.0
        weekly = np.ones(7)
    else:
        base = float(history["y"].tail(28).mean())
        history = history.copy()
        history["dow"] = history["ds"].dt.dayofweek
        weekly = (
            history.groupby("dow")["y"].mean() / max(base, 1.0)
        ).reindex(range(7), fill_value=1.0).values

    out = []
    for i in range(horizon):
        d = start + timedelta(days=i)
        geo = daily_seasonality_factor(d, business_type)
        yhat = base * float(weekly[d.weekday()]) * geo
        out.append(
            {
                "date": d.isoformat(),
                "yhat": round(max(0.0, yhat), 2),
                "yhat_lower": round(max(0.0, yhat * 0.75), 2),
                "yhat_upper": round(max(0.0, yhat * 1.2), 2),
            }
        )
    return out


def forecast_sales(
    daily_rows: List[dict],
    *,
    business_type: str = "other",
    horizon_days: int = 90,
    as_of: Optional[date] = None,
) -> dict:
    as_of = as_of or date.today()
    history = _prepare_history(daily_rows)
    forecast_start = as_of + timedelta(days=1)

    past = []
    if not history.empty:
        for _, row in history.iterrows():
            past.append(
                {
                    "date": row["ds"].date().isoformat(),
                    "revenue": round(float(row["y"]), 2),
                }
            )

    use_prophet = len(history) >= 14
    future_income: List[dict]
    model_name = "seasonal_baseline"

    prophet_available = False
    if use_prophet:
        try:
            from prophet import Prophet  # noqa: F401

            prophet_available = True
        except Exception:  # noqa: BLE001
            prophet_available = False

    if use_prophet and prophet_available:
        try:
            future_income = _prophet_forecast(history, horizon_days, business_type, forecast_start)
            model_name = "prophet"
        except Exception as exc:  # noqa: BLE001
            future_income = _fallback_forecast(
                history, horizon_days, business_type, forecast_start
            )
            model_name = f"fallback_after_prophet_error:{exc.__class__.__name__}"
    else:
        future_income = _fallback_forecast(
            history, horizon_days, business_type, forecast_start
        )
        model_name = "seasonal_baseline" if not prophet_available else "seasonal_baseline_thin_history"

    end = forecast_start + timedelta(days=horizon_days - 1)
    return {
        "model": model_name,
        "as_of": as_of.isoformat(),
        "horizon_days": horizon_days,
        "history": past,
        "income_forecast": future_income,
        "holiday_markers": holiday_markers(as_of - timedelta(days=30), end),
        "history_days": len(history),
    }


def _prophet_forecast(
    history: pd.DataFrame, horizon: int, business_type: str, start: date
) -> List[dict]:
    from prophet import Prophet

    df = history.copy()
    df["geo_factor"] = [
        daily_seasonality_factor(ts.date(), business_type) for ts in df["ds"]
    ]

    years = sorted({ts.year for ts in df["ds"]} | {start.year, start.year + 1})
    holidays = prophet_holiday_frame(years)

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=len(df) >= 120,
        seasonality_mode="multiplicative",
        interval_width=0.8,
        holidays=holidays if not holidays.empty else None,
    )
    model.add_regressor("geo_factor")
    model.fit(df[["ds", "y", "geo_factor"]])

    future = model.make_future_dataframe(periods=horizon)
    # Align future to start at `start` for the forecast portion
    future_only = pd.DataFrame(
        {"ds": pd.date_range(start=start, periods=horizon, freq="D")}
    )
    future_only["geo_factor"] = [
        daily_seasonality_factor(ts.date(), business_type) for ts in future_only["ds"]
    ]

    forecast = model.predict(future_only)
    out = []
    for _, row in forecast.iterrows():
        out.append(
            {
                "date": row["ds"].date().isoformat(),
                "yhat": round(max(0.0, float(row["yhat"])), 2),
                "yhat_lower": round(max(0.0, float(row["yhat_lower"])), 2),
                "yhat_upper": round(max(0.0, float(row["yhat_upper"])), 2),
            }
        )
    return out
