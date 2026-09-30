"""Sales forecasting with Facebook Prophet + Georgian Intelligence Layer."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .georgian_calendar import (
    daily_seasonality_factor,
    holiday_markers,
    prophet_holiday_frame,
)


def _prepare_history(daily_rows: List[dict]) -> pd.DataFrame:
    if not daily_rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(daily_rows)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["revenue"].astype(float).clip(lower=0)
    df = df.sort_values("ds").drop_duplicates("ds", keep="last")
    return df[["ds", "y"]].reset_index(drop=True)


def _fill_calendar(history: pd.DataFrame) -> pd.DataFrame:
    """Insert missing calendar days as 0 so closed days don't inflate averages."""
    if history.empty:
        return history
    idx = pd.date_range(history["ds"].min(), history["ds"].max(), freq="D")
    filled = history.set_index("ds").reindex(idx)
    filled["y"] = filled["y"].fillna(0.0)
    filled.index.name = "ds"
    return filled.reset_index()


def _winsorize(series: pd.Series, upper_q: float = 0.9) -> pd.Series:
    if series.empty:
        return series
    hi = float(series.quantile(upper_q))
    return series.clip(upper=hi)


def _level_and_weekly(history: pd.DataFrame) -> Tuple[float, np.ndarray, float, float, np.ndarray]:
    """
    Level uses ~90 days (3 months), not just the last 30.
    Last month can nudge the forecast but cannot dominate it.
    """
    if history.empty:
        return 100.0, np.ones(7), 100.0, 0.0, np.ones(7)

    filled = _fill_calendar(history)
    end = filled["ds"].max()
    # Prefer up to ~3 months of history for the sales level
    span = filled[filled["ds"] >= end - pd.Timedelta(days=89)].copy()
    if span.empty:
        span = filled.copy()

    last30 = filled[filled["ds"] >= end - pd.Timedelta(days=29)]
    mid30 = filled[
        (filled["ds"] >= end - pd.Timedelta(days=59))
        & (filled["ds"] < end - pd.Timedelta(days=29))
    ]
    old30 = filled[
        (filled["ds"] >= end - pd.Timedelta(days=89))
        & (filled["ds"] < end - pd.Timedelta(days=59))
    ]

    def _avg(block: pd.DataFrame) -> float | None:
        if block.empty:
            return None
        return float(block["y"].sum() / len(block))

    m1 = _avg(last30)   # most recent ~month
    m2 = _avg(mid30)
    m3 = _avg(old30)
    months = [m for m in (m3, m2, m1) if m is not None]
    raw_avg = float(span["y"].sum() / max(len(span), 1))

    # Multi-month blend: older months keep weight so one weak/strong month can't own the forecast
    if len(months) >= 3:
        # m3, m2, m1 → 35% / 35% / 30%
        calendar_level = 0.35 * m3 + 0.35 * m2 + 0.30 * m1
    elif len(months) == 2:
        calendar_level = 0.55 * months[0] + 0.45 * months[1]
    else:
        calendar_level = months[0] if months else raw_avg

    # If last month is an outlier vs the 3-month mean, pull harder toward the mean
    if m1 is not None and len(months) >= 2:
        multi_mean = float(np.mean(months))
        if multi_mean > 1 and (m1 > multi_mean * 1.15 or m1 < multi_mean * 0.85):
            calendar_level = 0.65 * multi_mean + 0.35 * m1

    span = span.copy()
    span["dow"] = span["ds"].dt.dayofweek
    open_prob = np.ones(7)
    for dow in range(7):
        days = span[span["dow"] == dow]
        if len(days):
            open_prob[dow] = float((days["y"] > 0).mean())
        else:
            open_prob[dow] = float((span["y"] > 0).mean()) if len(span) else 1.0
    open_prob = np.clip(open_prob, 0.05, 1.0)

    sold = span[span["y"] > 0].copy()
    if sold.empty:
        sold = span.copy()
    sold_y = _winsorize(sold["y"], 0.9)
    # Milder recency (half-life ~45d) so last month doesn't dominate open-day level
    ages = (sold["ds"].max() - sold["ds"]).dt.days.astype(float)
    weights = np.exp(-ages / 45.0)
    open_from_sales = float(np.average(sold_y, weights=weights))

    open_from_calendar = calendar_level / max(float(np.mean(open_prob)), 0.2)
    open_level = 0.55 * open_from_calendar + 0.45 * open_from_sales

    # Do NOT continue a one-month decline into the next month.
    # Only allow a tiny drift, and mean-revert after a cold/hot month.
    daily_drift = 0.0
    if m1 is not None and m2 is not None and m2 > 1:
        ratio = m1 / m2
        if ratio < 0.88:
            # weak last month → expect partial bounce toward multi-month level
            daily_drift = 0.002
        elif ratio > 1.15:
            daily_drift = -0.001

    sold = sold.copy()
    sold["y"] = _winsorize(sold["y"], 0.9)
    sold["dow"] = sold["ds"].dt.dayofweek
    dow_mean = sold.groupby("dow")["y"].mean()
    overall = float(dow_mean.mean()) if len(dow_mean) else max(open_level, 1.0)
    weekly = (dow_mean / max(overall, 1e-6)).reindex(range(7), fill_value=1.0).values
    weekly = np.clip(weekly, 0.7, 1.3)
    return max(0.0, open_level), weekly, raw_avg, daily_drift, open_prob


def _raw_forecast_from_params(
    *,
    base: float,
    weekly: np.ndarray,
    business_type: str,
    start: date,
    horizon: int,
    daily_drift: float = 0.0,
    open_prob: np.ndarray | None = None,
) -> List[dict]:
    if open_prob is None:
        open_prob = np.ones(7)
    out = []
    for i in range(horizon):
        d = start + timedelta(days=i)
        dow = d.weekday()
        geo = daily_seasonality_factor(d, business_type)
        geo_soft = 1.0 + (geo - 1.0) * 0.15
        level = base * ((1.0 + daily_drift) ** i)
        # Expected sales = open-day sales * P(open that weekday)
        yhat = level * float(weekly[dow]) * float(open_prob[dow]) * geo_soft
        out.append(
            {
                "date": d.isoformat(),
                "yhat": round(max(0.0, yhat), 2),
                "yhat_lower": round(max(0.0, yhat * 0.85), 2),
                "yhat_upper": round(max(0.0, yhat * 1.15), 2),
            }
        )
    return out


def _scale_forecast(rows: List[dict], scale: float) -> List[dict]:
    scale = float(np.clip(scale, 0.85, 1.0))
    out = []
    for r in rows:
        out.append(
            {
                "date": r["date"],
                "yhat": round(max(0.0, r["yhat"] * scale), 2),
                "yhat_lower": round(max(0.0, r["yhat_lower"] * scale), 2),
                "yhat_upper": round(max(0.0, r["yhat_upper"] * scale), 2),
            }
        )
    return out


def _backtest_scale(
    history: pd.DataFrame, business_type: str, holdout_days: int = 30
) -> Tuple[float, dict]:
    """
    Train on all but last holdout_days, predict that window, return
    actual/predicted scale factor and metrics.
    """
    filled = _fill_calendar(history)
    if len(filled) < holdout_days + 45:
        return 1.0, {"enabled": False, "reason": "not_enough_history"}

    cutoff = filled["ds"].max() - pd.Timedelta(days=holdout_days)
    train = filled[filled["ds"] <= cutoff][["ds", "y"]].copy()
    actual = filled[filled["ds"] > cutoff].copy()
    if train.empty or actual.empty:
        return 1.0, {"enabled": False, "reason": "empty_split"}

    base, weekly, _, drift, open_prob = _level_and_weekly(train)
    start = (cutoff + pd.Timedelta(days=1)).date()
    predicted = _raw_forecast_from_params(
        base=base,
        weekly=weekly,
        business_type=business_type,
        start=start,
        horizon=len(actual),
        daily_drift=drift,
        open_prob=open_prob,
    )
    pred_sum = sum(p["yhat"] for p in predicted)
    act_sum = float(actual["y"].sum())
    if pred_sum <= 1e-6:
        return 1.0, {"enabled": False, "reason": "zero_prediction"}

    scale = act_sum / pred_sum
    err_pct = abs(pred_sum - act_sum) / max(act_sum, 1e-6) * 100
    # Soft calibration: only correct over-prediction (never inflate future)
    soft = 1.0 + min(0.0, scale - 1.0) * 0.7
    return float(np.clip(soft, 0.85, 1.0)), {
        "enabled": True,
        "holdout_days": int(len(actual)),
        "actual_sum": round(act_sum, 2),
        "predicted_sum": round(pred_sum, 2),
        "error_pct": round(err_pct, 2),
        "raw_scale": round(float(scale), 4),
        "scale_applied": round(float(np.clip(soft, 0.85, 1.0)), 4),
        "holdout_start": actual["ds"].min().date().isoformat(),
        "holdout_end": actual["ds"].max().date().isoformat(),
        "note": "Backtest checks the last days already in your upload — not the future forecast cards. Upward calibration disabled.",
    }


def _fallback_forecast(
    history: pd.DataFrame, horizon: int, business_type: str, start: date
) -> Tuple[List[dict], dict]:
    base, weekly, raw_avg, drift, open_prob = _level_and_weekly(history)
    rows = _raw_forecast_from_params(
        base=base,
        weekly=weekly,
        business_type=business_type,
        start=start,
        horizon=horizon,
        daily_drift=drift,
        open_prob=open_prob,
    )
    # Backtest is diagnostic only. Applying its scale to the *next* month
    # wrongly copies last month's surprise (e.g. weak Sep) into Oct.
    _, backtest = _backtest_scale(history, business_type, holdout_days=30)
    meta = {
        "baseline_daily": round(base, 2),
        "recent_avg_raw": round(raw_avg, 2),
        "calibration_scale": 1.0,
        "backtest": backtest,
    }
    return rows, meta


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

    meta = {
        "baseline_daily": 0.0,
        "recent_avg_raw": 0.0,
        "calibration_scale": 1.0,
        "backtest": {"enabled": False},
    }
    future_income: List[dict]
    model_name = "seasonal_baseline"

    use_prophet = len(history) >= 21
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
            _, backtest = _backtest_scale(history, business_type, holdout_days=30)
            base, _, raw_avg, _, _ = _level_and_weekly(history)
            meta = {
                "baseline_daily": round(base, 2),
                "recent_avg_raw": round(raw_avg, 2),
                "calibration_scale": 1.0,
                "backtest": backtest,
            }
            model_name = "prophet"
        except Exception as exc:  # noqa: BLE001
            future_income, meta = _fallback_forecast(
                history, horizon_days, business_type, forecast_start
            )
            model_name = f"fallback_after_prophet_error:{exc.__class__.__name__}"
    else:
        future_income, meta = _fallback_forecast(
            history, horizon_days, business_type, forecast_start
        )
        model_name = "seasonal_baseline"

    end = forecast_start + timedelta(days=horizon_days - 1)
    return {
        "model": model_name,
        "as_of": as_of.isoformat(),
        "horizon_days": horizon_days,
        "history": past,
        "income_forecast": future_income,
        "holiday_markers": holiday_markers(as_of - timedelta(days=30), end),
        "history_days": len(history),
        "baseline_daily": meta["baseline_daily"],
        "recent_avg_raw": meta["recent_avg_raw"],
        "calibration_scale": meta["calibration_scale"],
        "backtest": meta["backtest"],
    }


def backtest_forecast(
    daily_rows: List[dict],
    *,
    business_type: str = "other",
    holdout_days: int = 30,
) -> dict:
    """Public backtest: train on all but last N days, score the holdout."""
    history = _prepare_history(daily_rows)
    if history.empty:
        return {"error": "No history"}
    filled = _fill_calendar(history)
    if len(filled) < holdout_days + 14:
        return {"error": f"Need at least {holdout_days + 14} calendar days"}

    cutoff = filled["ds"].max() - pd.Timedelta(days=holdout_days)
    train = filled[filled["ds"] <= cutoff]
    actual = filled[filled["ds"] > cutoff]
    as_of = cutoff.date()

    # Forecast WITHOUT nested holdout calibration (use raw params only)
    base, weekly, raw_avg, drift, open_prob = _level_and_weekly(train)
    pred = _raw_forecast_from_params(
        base=base,
        weekly=weekly,
        business_type=business_type,
        start=as_of + timedelta(days=1),
        horizon=holdout_days,
        daily_drift=drift,
        open_prob=open_prob,
    )[: len(actual)]

    # Also show calibrated version (what the live model would do on train only)
    calibrated = forecast_sales(
        [
            {"date": row["ds"].date().isoformat(), "revenue": float(row["y"])}
            for _, row in train.iterrows()
        ],
        business_type=business_type,
        horizon_days=holdout_days,
        as_of=as_of,
    )
    pred_cal = calibrated["income_forecast"][: len(actual)]

    pred_sum = sum(p["yhat"] for p in pred)
    pred_cal_sum = sum(p["yhat"] for p in pred_cal)
    act_sum = float(actual["y"].sum())
    mae = (
        float(np.mean([abs(float(a) - float(p["yhat"])) for a, p in zip(actual["y"].tolist(), pred_cal)]))
        if pred_cal
        else 0.0
    )
    return {
        "holdout_days": int(len(actual)),
        "train_days": int((train["y"] > 0).sum()),
        "train_calendar_days": int(len(train)),
        "actual_sum": round(act_sum, 2),
        "predicted_sum_raw": round(pred_sum, 2),
        "predicted_sum_calibrated": round(pred_cal_sum, 2),
        "error_pct_raw": round(abs(pred_sum - act_sum) / max(act_sum, 1e-6) * 100, 2),
        "error_pct_calibrated": round(abs(pred_cal_sum - act_sum) / max(act_sum, 1e-6) * 100, 2),
        "bias_pct_raw": round((pred_sum - act_sum) / max(act_sum, 1e-6) * 100, 2),
        "bias_pct_calibrated": round((pred_cal_sum - act_sum) / max(act_sum, 1e-6) * 100, 2),
        "mae_daily_calibrated": round(mae, 2),
        "baseline_daily": round(base, 2),
        "recent_avg_raw": round(raw_avg, 2),
        "calibration_scale": calibrated.get("calibration_scale"),
        "holdout_start": actual["ds"].min().date().isoformat(),
        "holdout_end": actual["ds"].max().date().isoformat(),
        "daily": [
            {
                "date": row["ds"].date().isoformat(),
                "actual": round(float(row["y"]), 2),
                "predicted_raw": pred[i]["yhat"] if i < len(pred) else None,
                "predicted_calibrated": pred_cal[i]["yhat"] if i < len(pred_cal) else None,
            }
            for i, (_, row) in enumerate(actual.iterrows())
        ],
    }


def _prophet_forecast(
    history: pd.DataFrame, horizon: int, business_type: str, start: date
) -> List[dict]:
    from prophet import Prophet

    filled = _fill_calendar(history)
    df = filled.copy()
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
