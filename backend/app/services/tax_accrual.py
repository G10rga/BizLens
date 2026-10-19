"""Helpers to accrue Georgian tax reserves when income is recorded."""

from __future__ import annotations

from datetime import date

from .georgian_tax import accrue_reserves, profile_from_business, tax_on_income
from .sales_agg import daily_rows_for_business


def ytd_before_date(business_id: int, sale_date: date) -> float:
    """YTD turnover strictly before sale_date (same calendar year)."""
    rows = daily_rows_for_business(business_id)
    year_start = date(sale_date.year, 1, 1)
    total = 0.0
    for row in rows:
        d = date.fromisoformat(row["date"])
        if year_start <= d < sale_date:
            total += float(row["revenue"] or 0)
    return round(total, 2)


def accrue_income_tax(business, amount: float, sale_date: date | None = None) -> dict:
    """Accrue tax/VAT reserves for a newly recorded income amount."""
    sale_date = sale_date or date.today()
    if not getattr(business, "tax_profile_complete", False):
        return {"income_tax_accrual": 0.0, "vat_accrual": 0.0}
    before = ytd_before_date(business.id, sale_date)
    # Same-day revenue already on DailySale should count as before this increment
    # when upsert already ran — include same-day prior total minus this amount.
    rows = daily_rows_for_business(business.id)
    same_day = 0.0
    for row in rows:
        if row["date"] == sale_date.isoformat():
            same_day = float(row["revenue"] or 0)
            break
    # If daily row already includes `amount`, subtract it so YTD-before is correct
    ytd = before + max(0.0, same_day - float(amount or 0))
    return accrue_reserves(business, float(amount or 0), sale_date, ytd)


def rebuild_tax_reserves(business) -> dict:
    """Recompute tax_reserve and vat_reserve from all DailySale history."""
    if not getattr(business, "tax_profile_complete", False):
        business.tax_reserve = 0.0
        business.vat_reserve = 0.0
        return {"tax_reserve": 0.0, "vat_reserve": 0.0}

    profile = profile_from_business(business)
    rows = daily_rows_for_business(business.id)
    tax_total = 0.0
    vat_total = 0.0
    ytd_by_year: dict[int, float] = {}

    for row in sorted(rows, key=lambda r: r["date"]):
        d = date.fromisoformat(row["date"])
        amount = float(row["revenue"] or 0)
        ytd_before = ytd_by_year.get(d.year, 0.0)
        result = tax_on_income(amount, ytd_before, profile)
        tax_total += result["income_tax_accrual"]
        vat_total += result["vat_accrual"]
        ytd_by_year[d.year] = ytd_before + result["taxable_turnover"]

    business.tax_reserve = round(tax_total, 2)
    business.vat_reserve = round(vat_total, 2)
    return {"tax_reserve": business.tax_reserve, "vat_reserve": business.vat_reserve}
