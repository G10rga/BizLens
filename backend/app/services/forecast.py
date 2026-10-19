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


# Dense CSV-like history: gaps between first/last sale are treated as closed (0).
# Sparse POS/Lens history: gaps are unregistered days — must NOT become zeros.
DENSE_COVERAGE_THRESHOLD = 0.80


def _prepare_history(daily_rows: List[dict]) -> pd.DataFrame:
    if not daily_rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(daily_rows)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["revenue"].astype(float).clip(lower=0)
    df = df.sort_values("ds").drop_duplicates("ds", keep="last")
    return df[["ds", "y"]].reset_index(drop=True)


def _reindex_calendar(history: pd.DataFrame) -> pd.DataFrame:
    """Full calendar between first and last sale; missing days have y=NaN, observed=False."""
    if history is None or history.empty:
        return pd.DataFrame(columns=["ds", "y", "observed"])
    src = history[["ds", "y"]].copy()
    idx = pd.date_range(src["ds"].min(), src["ds"].max(), freq="D")
    filled = src.set_index("ds").reindex(idx)
    filled["observed"] = filled["y"].notna()
    filled.index.name = "ds"
    return filled.reset_index()


def _coverage_ratio(cal: pd.DataFrame) -> float:
    if cal is None or cal.empty or "observed" not in cal.columns:
        return 0.0
    return float(cal["observed"].mean())


def _gaps_likely_closed(history: pd.DataFrame) -> bool:
    """
    True when recent history is dense enough that calendar gaps are probably
    real closed days (typical continuous CSV). False for sparse POS/Lens capture
    where missing days mean "not registered", not "sold 0".
    """
    cal = _reindex_calendar(history)
    if cal.empty:
        return True
    end = cal["ds"].max()
    span = cal[cal["ds"] >= end - pd.Timedelta(days=89)]
    if span.empty:
        span = cal
    return _coverage_ratio(span) >= DENSE_COVERAGE_THRESHOLD


def _fill_calendar(history: pd.DataFrame, *, force_zeros: bool | None = None) -> pd.DataFrame:
    """
    Expand history onto a continuous calendar.

    - Dense history: fill missing days with 0 (closed).
    - Sparse history: leave missing as NaN and keep ``observed=False`` so callers
      do not treat unregistered days as zero sales.
    """
    cal = _reindex_calendar(history)
    if cal.empty:
        return cal
    use_zeros = _gaps_likely_closed(history) if force_zeros is None else bool(force_zeros)
    out = cal.copy()
    if use_zeros:
        out["y"] = out["y"].fillna(0.0)
        # After filling, every calendar day is "known" for closed-day logic
        out["observed"] = True
    return out


def _is_sparse_frame(filled: pd.DataFrame) -> bool:
    if filled is None or filled.empty or "observed" not in filled.columns:
        return False
    return _coverage_ratio(filled) < DENSE_COVERAGE_THRESHOLD


def _observed_mask(df: pd.DataFrame) -> pd.Series:
    if "observed" in df.columns:
        return df["observed"].fillna(False).astype(bool)
    return df["y"].notna()


def _winsorize(series: pd.Series, upper_q: float = 0.9) -> pd.Series:
    if series.empty:
        return series
    hi = float(series.quantile(upper_q))
    return series.clip(upper=hi)


def _level_and_weekly(history: pd.DataFrame) -> Tuple[float, np.ndarray, float, float, np.ndarray]:
    """
    Level uses ~90 days (3 months), not just the last 30.
    Last month can nudge the forecast but cannot dominate it.

    Unregistered (missing) days are excluded from averages when history is sparse,
    so gaps do not drag the forecast toward zero.
    """
    if history.empty:
        return 100.0, np.ones(7), 100.0, 0.0, np.ones(7)

    filled = _fill_calendar(history)
    sparse = _is_sparse_frame(filled)
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
        if sparse:
            obs = block.loc[_observed_mask(block)]
            if obs.empty:
                return None
            # Mean of registered days only (never divide by missing calendar slots)
            return float(obs["y"].mean())
        return float(block["y"].sum() / len(block))

    m1 = _avg(last30)   # most recent ~month
    m2 = _avg(mid30)
    m3 = _avg(old30)
    months = [m for m in (m3, m2, m1) if m is not None]
    if sparse:
        obs_span = span.loc[_observed_mask(span)]
        raw_avg = float(obs_span["y"].mean()) if not obs_span.empty else 0.0
    else:
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
        if sparse:
            days = days.loc[_observed_mask(days)]
        if len(days) >= 2:
            open_prob[dow] = float((days["y"] > 0).mean())
        elif len(days) == 1:
            open_prob[dow] = 1.0 if float(days["y"].iloc[0]) > 0 else 0.05
        else:
            # No registered samples for this weekday → assume open (don't invent closures)
            open_prob[dow] = 1.0 if sparse else float((span["y"] > 0).mean()) if len(span) else 1.0
    open_prob = np.clip(open_prob, 0.05, 1.0)

    sold = span[span["y"] > 0].copy()
    if sold.empty:
        sold = span.loc[_observed_mask(span)].copy() if sparse else span.copy()
    if sold.empty:
        return max(0.0, calendar_level), np.ones(7), raw_avg, 0.0, open_prob
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


def _week_templates(filled: pd.DataFrame) -> list[np.ndarray]:
    """
    Extract real Mon–Sun sales vectors from history.

    Dense history: closed days stay 0.
    Sparse history: unregistered days are imputed from that weekday's typical
    open-day sales — never forced to 0 — so forecast weeks don't replay gaps.
    """
    if filled is None or filled.empty:
        return []
    df = filled.copy().sort_values("ds")
    positive = df["y"].notna() & (df["y"] > 0)
    first_sale = df.loc[positive, "ds"].min()
    last_sale = df.loc[positive, "ds"].max()
    if pd.isna(first_sale):
        return []
    sparse = _is_sparse_frame(df)
    df["dow"] = df["ds"].dt.dayofweek
    df["week_start"] = df["ds"] - pd.to_timedelta(df["dow"], unit="D")

    sold = df.loc[positive]
    dow_typical = sold.groupby("dow")["y"].mean() if not sold.empty else pd.Series(dtype=float)
    typical_fallback = float(dow_typical.mean()) if len(dow_typical) else 0.0

    templates: list[np.ndarray] = []
    for week_start, g in df.groupby("week_start", sort=True):
        ws = pd.Timestamp(week_start)
        we = ws + pd.Timedelta(days=6)
        # skip incomplete edge weeks
        if ws < first_sale.normalize() - pd.Timedelta(days=int(first_sale.dayofweek)):
            continue
        if we > last_sale.normalize() + pd.Timedelta(days=(6 - int(last_sale.dayofweek))):
            # allow last week if it contains the last sale
            if last_sale < ws or last_sale > we:
                continue

        if sparse:
            obs_count = int(_observed_mask(g).sum())
            if obs_count < 4:
                continue
            vec = np.zeros(7, dtype=float)
            for dow in range(7):
                day = g[g["dow"] == dow]
                if len(day) and bool(day["observed"].iloc[0]) and pd.notna(day["y"].iloc[0]):
                    vec[dow] = float(day["y"].iloc[0])
                else:
                    # Unregistered — impute typical open-day sales for that weekday
                    vec[dow] = float(dow_typical.get(dow, typical_fallback))
            open_days = int((vec > 0).sum())
            if open_days >= 4 and float(vec.sum()) > 0:
                templates.append(vec)
        else:
            by_dow = g.groupby("dow")["y"].sum()
            vec = by_dow.reindex(range(7), fill_value=0.0).to_numpy(dtype=float)
            open_days = int((vec > 0).sum())
            if open_days >= 4 and float(vec.sum()) > 0:
                templates.append(vec)
    return templates[-16:]


def _dow_bands(filled: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per-weekday low/high bands from history (p20 / p80)."""
    low = np.zeros(7)
    high = np.ones(7) * 100.0
    if filled is None or filled.empty:
        return low, high
    df = filled.copy()
    df["dow"] = df["ds"].dt.dayofweek
    sparse = _is_sparse_frame(df)
    for dow in range(7):
        subset = df[df["dow"] == dow]
        if sparse:
            subset = subset.loc[_observed_mask(subset)]
            # Bands from open days only — zeros from missing capture must not pull low→0
            vals = subset.loc[subset["y"] > 0, "y"].to_numpy(dtype=float)
        else:
            vals = subset["y"].dropna().to_numpy(dtype=float)
        if len(vals) == 0:
            continue
        low[dow] = float(np.percentile(vals, 20))
        high[dow] = float(np.percentile(vals, 80))
    return low, high


def _raw_forecast_from_params(
    *,
    base: float,
    weekly: np.ndarray,
    business_type: str,
    start: date,
    horizon: int,
    daily_drift: float = 0.0,
    open_prob: np.ndarray | None = None,
    history: pd.DataFrame | None = None,
) -> List[dict]:
    """
    Build daily forecast from *real* historical week shapes, scaled to the
    multi-month level — not a flat repeating weekday formula.
    """
    if open_prob is None:
        open_prob = np.ones(7)

    filled = _fill_calendar(history) if history is not None and not history.empty else None
    templates = _week_templates(filled) if filled is not None else []
    dow_low, dow_high = _dow_bands(filled) if filled is not None else (np.zeros(7), np.ones(7) * base)

    # Expected average daily from parametric level (for scaling templates)
    expected_daily = float(
        np.mean([base * float(weekly[d]) * float(open_prob[d]) for d in range(7)])
    )
    expected_daily = max(expected_daily, 1.0)

    # Scale all weeks by one global mean so stronger/weaker historical weeks
    # keep their relative amplitude (per-week normalize made every week identical).
    tmpl_avgs = [float(np.mean(t)) for t in templates if float(np.mean(t)) > 1e-6]
    global_tmpl_avg = float(np.mean(tmpl_avgs)) if tmpl_avgs else expected_daily
    global_tmpl_avg = max(global_tmpl_avg, 1e-6)

    # Same-weekday residual spread from history (for natural day-to-day wobble)
    dow_resid_std = np.zeros(7)
    if filled is not None and not filled.empty:
        tmp = filled.copy()
        tmp["dow"] = tmp["ds"].dt.dayofweek
        sparse = _is_sparse_frame(tmp)
        for dow in range(7):
            subset = tmp[tmp["dow"] == dow]
            if sparse:
                subset = subset.loc[_observed_mask(subset)]
                vals = subset.loc[subset["y"] > 0, "y"].to_numpy(dtype=float)
            else:
                vals = subset["y"].dropna().to_numpy(dtype=float)
            if len(vals) >= 4:
                dow_resid_std[dow] = float(np.std(vals)) * 0.15

    out: List[dict] = []
    for i in range(horizon):
        d = start + timedelta(days=i)
        dow = d.weekday()
        geo = daily_seasonality_factor(d, business_type)
        geo_soft = 1.0 + (geo - 1.0) * 0.25
        level_scale = ((1.0 + daily_drift) ** i) * geo_soft

        if templates:
            # Replay real weeks newest → older so successive forecast weeks differ
            tmpl = templates[-(1 + (i // 7) % len(templates))]
            week_scale = (expected_daily * level_scale) / global_tmpl_avg
            yhat = float(tmpl[dow]) * week_scale
            # Tiny deterministic wobble from historical same-dow spread (stable across runs)
            wobble = dow_resid_std[dow] * week_scale * (0.35 if (i + dow) % 3 == 0 else -0.2 if (i + dow) % 3 == 1 else 0.1)
            yhat = max(0.0, yhat + wobble)
            y_low = float(dow_low[dow]) * week_scale
            y_high = float(dow_high[dow]) * week_scale
            yhat_lower = min(yhat, y_low) * 0.55 + yhat * 0.45 * 0.88
            yhat_upper = max(yhat, y_high) * 0.55 + yhat * 0.45 * 1.12
            yhat_lower = min(yhat_lower, yhat * 0.9)
            yhat_upper = max(yhat_upper, yhat * 1.1)
        else:
            yhat = base * float(weekly[dow]) * float(open_prob[dow]) * level_scale
            yhat_lower = yhat * 0.85
            yhat_upper = yhat * 1.15

        out.append(
            {
                "date": d.isoformat(),
                "yhat": round(float(max(0.0, yhat)), 2),
                "yhat_lower": round(float(max(0.0, yhat_lower)), 2),
                "yhat_upper": round(float(max(0.0, yhat_upper)), 2),
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

    Scores only days that were actually registered in the holdout — unregistered
    gaps are not treated as actual zero sales.
    """
    filled = _fill_calendar(history)
    if len(filled) < holdout_days + 45:
        return 1.0, {"enabled": False, "reason": "not_enough_history"}

    cutoff = filled["ds"].max() - pd.Timedelta(days=holdout_days)
    keep_cols = ["ds", "y"] + (["observed"] if "observed" in filled.columns else [])
    train = filled[filled["ds"] <= cutoff][keep_cols].copy()
    actual = filled[filled["ds"] > cutoff].copy()
    if train.empty or actual.empty:
        return 1.0, {"enabled": False, "reason": "empty_split"}

    # Training history for level/templates: only observed points (drop NaN gaps)
    train_hist = train.loc[_observed_mask(train), ["ds", "y"]].copy() if "observed" in train.columns else train[["ds", "y"]]
    if train_hist.empty:
        train_hist = train[["ds", "y"]].dropna()
    if train_hist.empty:
        return 1.0, {"enabled": False, "reason": "empty_train"}

    base, weekly, _, drift, open_prob = _level_and_weekly(train_hist)
    start = (cutoff + pd.Timedelta(days=1)).date()
    predicted = _raw_forecast_from_params(
        base=base,
        weekly=weekly,
        business_type=business_type,
        start=start,
        horizon=len(actual),
        daily_drift=drift,
        open_prob=open_prob,
        history=train_hist,
    )
    pred_by_date = {p["date"]: p["yhat"] for p in predicted}
    # Compare only on registered holdout days
    scored = actual.loc[_observed_mask(actual)] if "observed" in actual.columns else actual.dropna(subset=["y"])
    if scored.empty:
        return 1.0, {"enabled": False, "reason": "no_observed_holdout"}
    act_sum = float(scored["y"].sum())
    pred_sum = float(
        sum(pred_by_date.get(row["ds"].date().isoformat(), 0.0) for _, row in scored.iterrows())
    )
    if pred_sum <= 1e-6:
        return 1.0, {"enabled": False, "reason": "zero_prediction"}

    scale = act_sum / pred_sum
    err_pct = abs(pred_sum - act_sum) / max(act_sum, 1e-6) * 100
    # Soft calibration: only correct over-prediction (never inflate future)
    soft = 1.0 + min(0.0, scale - 1.0) * 0.7
    return float(np.clip(soft, 0.85, 1.0)), {
        "enabled": True,
        "holdout_days": int(len(scored)),
        "actual_sum": round(act_sum, 2),
        "predicted_sum": round(pred_sum, 2),
        "error_pct": round(err_pct, 2),
        "raw_scale": round(float(scale), 4),
        "scale_applied": round(float(np.clip(soft, 0.85, 1.0)), 4),
        "holdout_start": scored["ds"].min().date().isoformat(),
        "holdout_end": scored["ds"].max().date().isoformat(),
        "note": "Backtest checks registered holdout days only (unregistered gaps ignored). Upward calibration disabled.",
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
        history=history,
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
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

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
            # Hard timeout — Stan can look "stuck" for a long time on Windows
            with ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(
                    _prophet_forecast,
                    history,
                    horizon_days,
                    business_type,
                    forecast_start,
                )
                future_income = fut.result(timeout=20)
            _, backtest = _backtest_scale(history, business_type, holdout_days=30)
            base, _, raw_avg, _, _ = _level_and_weekly(history)
            meta = {
                "baseline_daily": round(base, 2),
                "recent_avg_raw": round(raw_avg, 2),
                "calibration_scale": 1.0,
                "backtest": backtest,
            }
            model_name = "prophet"
        except FuturesTimeout:
            future_income, meta = _fallback_forecast(
                history, horizon_days, business_type, forecast_start
            )
            model_name = "seasonal_baseline_after_prophet_timeout"
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

    train_hist = (
        train.loc[_observed_mask(train), ["ds", "y"]].copy()
        if "observed" in train.columns
        else train[["ds", "y"]].dropna()
    )
    if train_hist.empty:
        return {"error": "No observed training days"}

    # Forecast WITHOUT nested holdout calibration (use raw params only)
    base, weekly, raw_avg, drift, open_prob = _level_and_weekly(train_hist)
    pred = _raw_forecast_from_params(
        base=base,
        weekly=weekly,
        business_type=business_type,
        start=as_of + timedelta(days=1),
        horizon=holdout_days,
        daily_drift=drift,
        open_prob=open_prob,
        history=train_hist,
    )

    # Also show calibrated version (what the live model would do on train only)
    calibrated = forecast_sales(
        [
            {"date": row["ds"].date().isoformat(), "revenue": float(row["y"])}
            for _, row in train_hist.iterrows()
        ],
        business_type=business_type,
        horizon_days=holdout_days,
        as_of=as_of,
    )
    pred_cal = calibrated["income_forecast"]
    pred_by = {p["date"]: p["yhat"] for p in pred}
    pred_cal_by = {p["date"]: p["yhat"] for p in pred_cal}

    scored = (
        actual.loc[_observed_mask(actual)].copy()
        if "observed" in actual.columns
        else actual.dropna(subset=["y"]).copy()
    )
    if scored.empty:
        return {"error": "No observed holdout days"}

    act_sum = float(scored["y"].sum())
    pred_sum = float(sum(pred_by.get(r["ds"].date().isoformat(), 0.0) for _, r in scored.iterrows()))
    pred_cal_sum = float(
        sum(pred_cal_by.get(r["ds"].date().isoformat(), 0.0) for _, r in scored.iterrows())
    )
    mae = float(
        np.mean(
            [
                abs(float(r["y"]) - float(pred_cal_by.get(r["ds"].date().isoformat(), 0.0)))
                for _, r in scored.iterrows()
            ]
        )
    )
    return {
        "holdout_days": int(len(scored)),
        "train_days": int((train_hist["y"] > 0).sum()),
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
        "holdout_start": scored["ds"].min().date().isoformat(),
        "holdout_end": scored["ds"].max().date().isoformat(),
        "daily": [
            {
                "date": row["ds"].date().isoformat(),
                "actual": round(float(row["y"]), 2),
                "predicted_raw": pred_by.get(row["ds"].date().isoformat()),
                "predicted_calibrated": pred_cal_by.get(row["ds"].date().isoformat()),
            }
            for _, row in scored.iterrows()
        ],
    }


def _prophet_forecast(
    history: pd.DataFrame, horizon: int, business_type: str, start: date
) -> List[dict]:
    from prophet import Prophet

    # Fit on observed sales only. Zero-filled closed days + multiplicative
    # seasonality makes Stan slow and can inflate forecasts.
    df = history[history["y"] > 0].copy()
    if len(df) < 21:
        df = history.copy()
    df["geo_factor"] = [
        daily_seasonality_factor(ts.date(), business_type) for ts in df["ds"]
    ]

    years = sorted({ts.year for ts in df["ds"]} | {start.year, start.year + 1})
    holidays = prophet_holiday_frame(years)

    # Yearly Fourier terms need ~2 years; with <730d they are under-identified.
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=len(df) >= 730,
        seasonality_mode="additive",
        interval_width=0.5,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=5.0,
        holidays=holidays if not holidays.empty else None,
    )
    model.add_regressor("geo_factor", prior_scale=0.5, mode="additive")
    model.fit(df[["ds", "y", "geo_factor"]])

    future_only = pd.DataFrame(
        {"ds": pd.date_range(start=start, periods=horizon, freq="D")}
    )
    future_only["geo_factor"] = [
        daily_seasonality_factor(ts.date(), business_type) for ts in future_only["ds"]
    ]

    forecast = model.predict(future_only)
    # Soft cap so a bad fit can't show absurd daily sales
    hist_hi = float(df["y"].quantile(0.95)) if len(df) else 200.0
    cap = max(hist_hi * 1.6, 50.0)

    out = []
    for _, row in forecast.iterrows():
        yhat = min(max(0.0, float(row["yhat"])), cap)
        y_lo = min(max(0.0, float(row["yhat_lower"])), cap)
        y_hi = min(max(0.0, float(row["yhat_upper"])), max(cap, yhat))
        out.append(
            {
                "date": row["ds"].date().isoformat(),
                "yhat": round(yhat, 2),
                "yhat_lower": round(min(y_lo, yhat), 2),
                "yhat_upper": round(max(y_hi, yhat), 2),
            }
        )
    return out
