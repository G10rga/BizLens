"""Cash-flow projection: predicted income minus known expenses."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Dict, List, Tuple

from ..config import Config


def _clamp_due_day(year: int, month: int, due_day: int) -> date:
    last = monthrange(year, month)[1]
    return date(year, month, min(due_day, last))


def expand_fixed_expenses(
    expenses: List[dict], start: date, end: date
) -> Dict[date, List[dict]]:
    """Map date -> list of expense events for monthly fixed costs."""
    by_day: Dict[date, List[dict]] = {}
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        for exp in expenses:
            due = _clamp_due_day(cursor.year, cursor.month, int(exp["due_day"]))
            if start <= due <= end:
                by_day.setdefault(due, []).append(
                    {
                        "type": "fixed",
                        "name": exp["name"],
                        "amount": float(exp["amount"]),
                    }
                )
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return by_day


def expand_supplier_payments(
    suppliers: List[dict], start: date, end: date
) -> Dict[date, List[dict]]:
    by_day: Dict[date, List[dict]] = {}
    for sup in suppliers:
        due = date.fromisoformat(sup["next_due_date"]) if isinstance(sup["next_due_date"], str) else sup["next_due_date"]
        every = max(1, int(sup["every_n_days"]))
        # Walk backward to cover window start
        while due > start:
            due -= timedelta(days=every)
        while due < start:
            due += timedelta(days=every)
        while due <= end:
            by_day.setdefault(due, []).append(
                {
                    "type": "supplier",
                    "name": sup["name"],
                    "amount": float(sup["amount"]),
                }
            )
            due += timedelta(days=every)
    return by_day


def merge_expense_maps(*maps: Dict[date, List[dict]]) -> Dict[date, List[dict]]:
    out: Dict[date, List[dict]] = {}
    for m in maps:
        for d, items in m.items():
            out.setdefault(d, []).extend(items)
    return out


def project_cashflow(
    *,
    starting_cash: float,
    start_date: date,
    horizon_days: int,
    income_series: List[dict],
    expenses: List[dict],
    suppliers: List[dict],
) -> dict:
    """
    income_series items: {date, yhat, yhat_lower, yhat_upper}
    Returns timeline for most_likely / best / worst cash paths.
    """
    end = start_date + timedelta(days=horizon_days - 1)
    expense_map = merge_expense_maps(
        expand_fixed_expenses(expenses, start_date, end),
        expand_supplier_payments(suppliers, start_date, end),
    )

    income_by_date = {date.fromisoformat(i["date"]) if isinstance(i["date"], str) else i["date"]: i for i in income_series}

    cash_likely = starting_cash
    cash_best = starting_cash
    cash_worst = starting_cash

    timeline = []
    expense_markers = []

    for offset in range(horizon_days):
        d = start_date + timedelta(days=offset)
        inc = income_by_date.get(
            d, {"yhat": 0.0, "yhat_lower": 0.0, "yhat_upper": 0.0}
        )
        day_expenses = expense_map.get(d, [])
        expense_total = sum(e["amount"] for e in day_expenses)

        if day_expenses:
            expense_markers.append(
                {
                    "date": d.isoformat(),
                    "amount": expense_total,
                    "items": day_expenses,
                }
            )

        cash_likely += float(inc["yhat"]) - expense_total
        cash_best += float(inc["yhat_upper"]) - expense_total
        cash_worst += float(inc["yhat_lower"]) - expense_total

        zone = _zone(cash_likely)
        timeline.append(
            {
                "date": d.isoformat(),
                "income_likely": round(float(inc["yhat"]), 2),
                "income_best": round(float(inc["yhat_upper"]), 2),
                "income_worst": round(float(inc["yhat_lower"]), 2),
                "expenses": round(expense_total, 2),
                "cash_likely": round(cash_likely, 2),
                "cash_best": round(cash_best, 2),
                "cash_worst": round(cash_worst, 2),
                "zone": zone,
            }
        )

    n30 = min(len(timeline), 30)
    sales_30 = _sales_sum(timeline, 30, "income_likely")
    sales_60 = _sales_sum(timeline, 60, "income_likely")
    sales_90 = _sales_sum(timeline, 90, "income_likely")
    sales_30_low, sales_30_high = _tight_total_range(
        sales_30,
        _sales_sum(timeline, 30, "income_worst"),
        _sales_sum(timeline, 30, "income_best"),
    )
    sales_60_low, sales_60_high = _tight_total_range(
        sales_60,
        _sales_sum(timeline, 60, "income_worst"),
        _sales_sum(timeline, 60, "income_best"),
    )
    sales_90_low, sales_90_high = _tight_total_range(
        sales_90,
        _sales_sum(timeline, 90, "income_worst"),
        _sales_sum(timeline, 90, "income_best"),
    )

    cash_30 = _cash_at(timeline, 29)
    cash_60 = _cash_at(timeline, 59)
    cash_30_low, cash_30_high = _tight_total_range(
        cash_30,
        _cash_at(timeline, 29, "cash_worst"),
        _cash_at(timeline, 29, "cash_best"),
        max_pct=0.15,
    )
    cash_60_low, cash_60_high = _tight_total_range(
        cash_60,
        _cash_at(timeline, 59, "cash_worst"),
        _cash_at(timeline, 59, "cash_best"),
        max_pct=0.15,
    )

    summary = {
        "cash_today": round(starting_cash, 2),
        "cash_30": cash_30,
        "cash_60": cash_60,
        "cash_90": _cash_at(timeline, min(len(timeline) - 1, 89)),
        "cash_30_low": cash_30_low,
        "cash_30_high": cash_30_high,
        "cash_60_low": cash_60_low,
        "cash_60_high": cash_60_high,
        "sales_30": sales_30,
        "sales_30_low": sales_30_low,
        "sales_30_high": sales_30_high,
        "sales_60": sales_60,
        "sales_60_low": sales_60_low,
        "sales_60_high": sales_60_high,
        "sales_90": sales_90,
        "sales_90_low": sales_90_low,
        "sales_90_high": sales_90_high,
        "avg_daily_sales": round((sales_30 or 0) / max(n30, 1), 2),
        "avg_daily_sales_low": round((sales_30_low or 0) / max(n30, 1), 2),
        "avg_daily_sales_high": round((sales_30_high or 0) / max(n30, 1), 2),
        "days_until_danger": _days_until_danger(timeline),
    }

    return {
        "timeline": timeline,
        "expense_markers": expense_markers,
        "summary": summary,
    }


def _zone(cash: float) -> str:
    if cash > Config.CASH_GREEN_THRESHOLD:
        return "green"
    if cash >= Config.CASH_YELLOW_THRESHOLD:
        return "yellow"
    return "red"


def _cash_at(timeline: List[dict], idx: int, key: str = "cash_likely") -> float | None:
    if idx < 0 or idx >= len(timeline):
        return None
    return timeline[idx][key]


def _sales_sum(timeline: List[dict], days: int, key: str = "income_likely") -> float | None:
    if not timeline:
        return None
    chunk = timeline[:days]
    return round(sum(row[key] for row in chunk), 2)


def _tight_total_range(
    likely: float | None,
    raw_low: float | None,
    raw_high: float | None,
    *,
    shrink: float = 0.28,
    min_pct: float = 0.05,
    max_pct: float = 0.12,
) -> tuple[float | None, float | None]:
    """
    Monthly card ranges: summing every day's low/high assumes all days hit
    extremes together and looks absurdly wide. Shrink toward the likely total
    and clamp to about ±5–12%.
    """
    if likely is None:
        return raw_low, raw_high
    lo_src = raw_low if raw_low is not None else likely
    hi_src = raw_high if raw_high is not None else likely
    lo = likely - (likely - lo_src) * shrink
    hi = likely + (hi_src - likely) * shrink
    lo = max(lo, likely * (1.0 - max_pct))
    hi = min(hi, likely * (1.0 + max_pct))
    lo = min(lo, likely * (1.0 - min_pct))
    hi = max(hi, likely * (1.0 + min_pct))
    return round(lo, 2), round(hi, 2)


def _days_until_danger(timeline: List[dict]) -> int | None:
    for i, row in enumerate(timeline):
        if row["zone"] == "red":
            return i
    return None
