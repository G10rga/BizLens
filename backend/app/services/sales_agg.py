"""Helpers to keep DailySale aggregates in sync with POS sales."""

from __future__ import annotations

from datetime import date, datetime

from ..extensions import db
from ..models import DailySale, Sale


def upsert_daily_revenue(business_id: int, sale_date: date, delta: float, source: str = "pos") -> DailySale:
    row = DailySale.query.filter_by(business_id=business_id, sale_date=sale_date).first()
    if row is None:
        row = DailySale(
            business_id=business_id,
            sale_date=sale_date,
            revenue=max(0.0, float(delta)),
            source=source,
        )
        db.session.add(row)
    else:
        row.revenue = max(0.0, float(row.revenue) + float(delta))
        row.source = source if row.source == source else "mixed"
    return row


def set_daily_revenue(business_id: int, sale_date: date, revenue: float, source: str = "csv") -> DailySale:
    row = DailySale.query.filter_by(business_id=business_id, sale_date=sale_date).first()
    if row is None:
        row = DailySale(
            business_id=business_id,
            sale_date=sale_date,
            revenue=float(revenue),
            source=source,
        )
        db.session.add(row)
    else:
        row.revenue = float(revenue)
        row.source = source
    return row


def daily_rows_for_business(business_id: int) -> list[dict]:
    rows = (
        DailySale.query.filter_by(business_id=business_id)
        .order_by(DailySale.sale_date.asc())
        .all()
    )
    return [{"date": r.sale_date.isoformat(), "revenue": r.revenue} for r in rows]


def today_sales_summary(business_id: int, day: date | None = None) -> dict:
    day = day or date.today()
    start = datetime.combine(day, datetime.min.time())
    end = datetime.combine(day, datetime.max.time())
    sales = (
        Sale.query.filter(
            Sale.business_id == business_id,
            Sale.sold_at >= start,
            Sale.sold_at <= end,
        )
        .order_by(Sale.sold_at.desc())
        .all()
    )
    cash_total = sum(s.total for s in sales if s.payment_method == "cash")
    card_total = sum(s.total for s in sales if s.payment_method == "card")
    pos_total = round(sum(s.total for s in sales), 2)

    daily = DailySale.query.filter_by(business_id=business_id, sale_date=day).first()
    imported_total = round(float(daily.revenue), 2) if daily else 0.0
    # Prefer explicit POS sum when tickets exist; otherwise show imported day total
    display_total = pos_total if sales else imported_total

    return {
        "date": day.isoformat(),
        "count": len(sales),
        "total": display_total,
        "pos_total": pos_total,
        "imported_daily_total": imported_total,
        "daily_source": daily.source if daily else None,
        "cash_total": round(cash_total, 2),
        "card_total": round(card_total, 2),
        "sales": [s.to_dict() for s in sales],
    }
