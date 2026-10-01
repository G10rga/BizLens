"""Lens Mode data-completeness indicators for forecast confidence."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..models import ReceiptCapture


def completeness_report(business, days: int = 14) -> dict:
    days = max(1, min(int(days), 60))
    expected = max(1, int(business.lens_expected_receipts_per_day or 10))
    end = date.today()
    start = end - timedelta(days=days - 1)

    captures = (
        ReceiptCapture.query.filter(
            ReceiptCapture.business_id == business.id,
            ReceiptCapture.status == "confirmed",
            ReceiptCapture.receipt_date >= start,
            ReceiptCapture.receipt_date <= end,
        )
        .all()
    )

    by_day: dict[str, int] = {}
    for cap in captures:
        if not cap.receipt_date:
            continue
        key = cap.receipt_date.isoformat()
        by_day[key] = by_day.get(key, 0) + 1

    daily = []
    rates = []
    for offset in range(days):
        d = start + timedelta(days=offset)
        key = d.isoformat()
        captured = by_day.get(key, 0)
        rate = min(1.0, captured / expected)
        rates.append(rate)
        # Wider band when capture rate is low: 1.0 = full confidence shrink factor
        confidence = round(0.35 + 0.65 * rate, 3)
        range_widen = round(1.0 + (1.0 - rate) * 0.8, 3)
        daily.append(
            {
                "date": key,
                "captured": captured,
                "expected": expected,
                "capture_rate": round(rate, 3),
                "confidence": confidence,
                "range_widen_factor": range_widen,
            }
        )

    avg_rate = sum(rates) / len(rates) if rates else 0.0
    today_key = end.isoformat()
    today = next((row for row in daily if row["date"] == today_key), None)

    return {
        "expected_per_day": expected,
        "days": days,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "average_capture_rate": round(avg_rate, 3),
        "average_confidence": round(0.35 + 0.65 * avg_rate, 3),
        "range_widen_factor": round(1.0 + (1.0 - avg_rate) * 0.8, 3),
        "today": today,
        "daily": daily,
        "note": (
            "Lower capture rates widen forecast ranges. "
            "Photograph every fiscal receipt for tighter confidence bands."
        ),
    }


def recent_capture_widen_factor(business, lookback_days: int = 7) -> float:
    report = completeness_report(business, days=lookback_days)
    return float(report.get("range_widen_factor") or 1.0)
