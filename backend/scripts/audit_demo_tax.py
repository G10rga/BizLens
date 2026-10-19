"""Audit Georgian tax calculations against the demo account.

Run from backend/:  python scripts/audit_demo_tax.py
"""

from __future__ import annotations

import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Business, DailySale, FixedExpense, Product, Sale, SaleItem, User  # noqa: E402
from app.seed import DEMO_EMAIL, DEMO_PASSWORD  # noqa: E402
from app.services.georgian_calendar import daily_seasonality_factor  # noqa: E402
from app.services.georgian_tax import (  # noqa: E402
    GENERAL_PIT_RATE,
    GENERAL_PROFIT_MARGIN,
    LLC_DISTRIBUTION_EFFECTIVE,
    LLC_DRAW_SHARE_OF_NET,
    SMALL_OVER_CAP_RATE,
    SMALL_RATE,
    SMALL_TURNOVER_CAP,
    VAT_RATE,
    estimate_period,
    expand_tax_payments,
    profile_from_business,
    resolve_obligations,
    tax_on_income,
    validate_profile,
    ytd_turnover,
)
from app.services.sales_agg import daily_rows_for_business, upsert_daily_revenue  # noqa: E402
from app.services.tax_accrual import rebuild_tax_reserves  # noqa: E402

ISSUES: list[str] = []
OKS: list[str] = []


def approx(a: float, b: float, tol: float = 0.02) -> bool:
    return abs(float(a) - float(b)) <= tol


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        OKS.append(name)
        print(f"  OK  {name}" + (f" â€” {detail}" if detail else ""))
    else:
        ISSUES.append(f"{name}: {detail}")
        print(f" FAIL {name} â€” {detail}")


def test_unit_math() -> None:
    print("\n=== Unit: tax_on_income ===")
    # Small 1%
    r = tax_on_income(1000, 0, {"legal_form": "ie", "tax_regime": "small", "is_vat_payer": False})
    check("small 1% of 1000", approx(r["income_tax_accrual"], 10.0), str(r))

    # Small crosses 500k â†’ split 1%/3%
    r = tax_on_income(1000, SMALL_TURNOVER_CAP - 200, {
        "legal_form": "ie", "tax_regime": "small", "is_vat_payer": False
    })
    expected = round(200 * SMALL_RATE + 800 * SMALL_OVER_CAP_RATE, 2)
    check("small split at 500k", approx(r["income_tax_accrual"], expected), f"got {r} expected {expected}")

    # Micro 0
    r = tax_on_income(500, 0, {"legal_form": "ie", "tax_regime": "micro", "is_vat_payer": False})
    check("micro 0%", r["income_tax_accrual"] == 0 and r["vat_accrual"] == 0, str(r))

    # General IE 20% on 25% margin
    r = tax_on_income(1000, 0, {"legal_form": "ie", "tax_regime": "general", "is_vat_payer": False})
    exp = round(1000 * GENERAL_PROFIT_MARGIN * GENERAL_PIT_RATE, 2)
    check("general IE", approx(r["income_tax_accrual"], exp), str(r))

    # VAT inclusive 118 â†’ VAT 18, net 100
    r = tax_on_income(118, 0, {
        "legal_form": "ie", "tax_regime": "general", "is_vat_payer": True
    })
    check("VAT 18/118", approx(r["vat_accrual"], 18.0) and approx(r["taxable_turnover"], 100.0), str(r))
    exp = round(100 * GENERAL_PROFIT_MARGIN * GENERAL_PIT_RATE, 2)
    check("general on net after VAT", approx(r["income_tax_accrual"], exp), str(r))

    # LLC no draws â†’ only VAT
    r = tax_on_income(118, 0, {
        "legal_form": "llc", "tax_regime": "llc_estonian", "is_vat_payer": True,
        "llc_distributes_profit": False,
    })
    check("LLC retain: no CIT reserve", r["income_tax_accrual"] == 0 and approx(r["vat_accrual"], 18.0), str(r))

    # LLC draws: 50% net * 19.25%
    r = tax_on_income(118, 0, {
        "legal_form": "llc", "tax_regime": "llc_estonian", "is_vat_payer": True,
        "llc_distributes_profit": True,
    })
    exp_llc = round(100 * LLC_DRAW_SHARE_OF_NET * LLC_DISTRIBUTION_EFFECTIVE, 2)
    check("LLC draw tax", approx(r["income_tax_accrual"], exp_llc) and approx(r["vat_accrual"], 18.0), str(r))

    # Small + VAT invalid
    ready, errs, _ = validate_profile({
        "legal_form": "ie", "tax_regime": "small", "is_vat_payer": True, "has_employees": False
    })
    check("reject small+VAT", ready is None and bool(errs), str(errs))

    # Micro + employees invalid
    ready, errs, _ = validate_profile({
        "legal_form": "ie", "tax_regime": "micro", "is_vat_payer": False, "has_employees": True
    })
    check("reject micro+employees", ready is None and bool(errs), str(errs))

    # estimate_period: general matches accrual margin; pension excluded from gap
    gen = estimate_period(
        profile={"legal_form": "ie", "tax_regime": "general", "is_vat_payer": False,
                 "has_employees": False, "pension_participants": False,
                 "llc_distributes_profit": False},
        income_total=1000,
        expense_total=900,  # high expenses must NOT change general estimate
        tax_reserve=50,
        vat_reserve=0,
        cash_on_hand=500,
        ytd_turnover_value=1000,
        rolling_12m=1000,
    )
    check(
        "general estimate uses 25% margin not expenses",
        approx(gen["estimated_income_tax"], 50.0),
        str(gen["estimated_income_tax"]),
    )
    check("general fully reserved -> gap 0", gen["still_to_set_aside"] == 0)

    pen = estimate_period(
        profile={"legal_form": "ie", "tax_regime": "small", "is_vat_payer": False,
                 "has_employees": True, "pension_participants": True,
                 "llc_distributes_profit": False},
        income_total=10000,
        expense_total=5000,
        salary_expense_total=32000,
        tax_reserve=100,
        vat_reserve=0,
        cash_on_hand=2000,
        ytd_turnover_value=10000,
        rolling_12m=10000,
    )
    check(
        "pension in total but not in still_to_set_aside",
        approx(pen["estimated_income_tax"], 100.0)
        and approx(pen["employer_pension_estimate"], 640.0)
        and approx(pen["estimated_total_tax"], 740.0)
        and pen["still_to_set_aside"] == 0,
        str({k: pen[k] for k in (
            "estimated_income_tax", "employer_pension_estimate",
            "estimated_total_tax", "still_to_set_aside"
        )}),
    )


def repair_demo_history(business: Business) -> None:
    """Re-seed daily revenue if wiped, keep tax profile IE/small."""
    count = DailySale.query.filter_by(business_id=business.id).count()
    if count > 0:
        print(f"\nDemo already has {count} DailySale rows")
        return

    print("\nRepairing demo: regenerating ~120 days of DailySaleâ€¦")
    random.seed(42)
    today = date.today()
    base = 420.0
    products = Product.query.filter_by(business_id=business.id, active=True).all()
    for i in range(120, 0, -1):
        d = today - timedelta(days=i)
        dow = d.weekday()
        weekly = [0.85, 0.9, 0.95, 1.0, 1.15, 1.35, 1.2][dow]
        geo = daily_seasonality_factor(d, "bakery")
        noise = 1.0 + random.uniform(-0.12, 0.12)
        trend = 1.0 + (120 - i) * 0.0008
        revenue = round(base * weekly * geo * noise * trend, 2)
        upsert_daily_revenue(business.id, d, revenue, source="seed")
        if i <= 3 and products:
            # light POS samples
            p = products[0]
            sale = Sale(
                business_id=business.id,
                total=min(revenue, p.price * 2),
                payment_method="cash",
                sold_at=datetime.combine(d, datetime.min.time()) + timedelta(hours=12),
                source="pos",
            )
            db.session.add(sale)
            db.session.flush()
            db.session.add(SaleItem(
                sale_id=sale.id, product_id=p.id, product_name=p.name,
                unit_price=p.price, quantity=2, line_total=round(p.price * 2, 2),
            ))

    # Baseline = start of seeded history so reserve rebuild is meaningful for demo
    business.cash_baseline_date = today - timedelta(days=120)
    business.cash_on_hand = 1850.0
    business.legal_form = "ie"
    business.tax_regime = "small"
    business.is_vat_payer = False
    business.has_employees = True
    business.pension_participants = True
    business.llc_distributes_profit = False
    business.tax_profile_complete = True
    rebuild_tax_reserves(business)
    db.session.commit()
    print("  repaired: days=", DailySale.query.filter_by(business_id=business.id).count(),
          "reserve=", business.tax_reserve, "baseline=", business.cash_baseline_date)


def audit_demo(business: Business) -> None:
    print("\n=== Demo account state ===")
    rows = daily_rows_for_business(business.id)
    profile = profile_from_business(business)
    print("profile", profile)
    print("cash", business.cash_on_hand, "baseline", business.cash_baseline_date)
    print("reserves tax/vat", business.tax_reserve, business.vat_reserve)
    print("history days", len(rows), "sum", round(sum(r["revenue"] for r in rows), 2))

    check("demo tax profile complete", bool(business.tax_profile_complete))
    check("demo is IE small non-VAT", profile["tax_regime"] == "small" and not profile["is_vat_payer"])
    check("demo has sales history", len(rows) >= 30, f"days={len(rows)}")

    # Rebuild consistency: reserve == sum of tax_on_income since baseline
    baseline = business.cash_baseline_date or date.today()
    ytd_by_year: dict[int, float] = {}
    tax_sum = 0.0
    vat_sum = 0.0
    for row in sorted(rows, key=lambda r: r["date"]):
        d = date.fromisoformat(row["date"])
        amt = float(row["revenue"])
        ytd_before = ytd_by_year.get(d.year, 0.0)
        part = tax_on_income(amt, ytd_before, profile)
        ytd_by_year[d.year] = ytd_before + part["taxable_turnover"]
        if d >= baseline:
            tax_sum += part["income_tax_accrual"]
            vat_sum += part["vat_accrual"]
    tax_sum, vat_sum = round(tax_sum, 2), round(vat_sum, 2)
    check(
        "rebuild matches manual sum since baseline",
        approx(business.tax_reserve or 0, tax_sum) and approx(business.vat_reserve or 0, vat_sum),
        f"db=({business.tax_reserve},{business.vat_reserve}) manual=({tax_sum},{vat_sum})",
    )

    # For IE small: reserve â‰ˆ 1% of revenue since baseline (if under 500k)
    since = [r for r in rows if date.fromisoformat(r["date"]) >= baseline]
    rev_since = round(sum(r["revenue"] for r in since), 2)
    if rev_since <= SMALL_TURNOVER_CAP:
        exp_tax = round(rev_since * SMALL_RATE, 2)
        check(
            "IE small reserve â‰ˆ 1% of post-baseline revenue",
            approx(tax_sum, exp_tax, tol=1.0),
            f"1%={exp_tax} reserve={tax_sum} revenue_since={rev_since}",
        )

    # estimate_period vs profile
    exps = [e.to_dict() for e in FixedExpense.query.filter_by(business_id=business.id).all()]
    salary = sum(e["amount"] for e in exps if e["name"] == "salaries")
    # expand salaries over YTD months roughly
    as_of = date.today()
    ytd_rev = ytd_turnover(rows, as_of)
    # count salary months in YTD from expense expansion would be better; use estimate API path
    from app.services.cashflow import expand_fixed_expenses, expand_supplier_payments, merge_expense_maps
    from app.models import SupplierPayment
    suppliers = [s.to_dict() for s in SupplierPayment.query.filter_by(business_id=business.id).all()]
    year_start = date(as_of.year, 1, 1)
    merged = merge_expense_maps(
        expand_fixed_expenses(exps, year_start, as_of),
        expand_supplier_payments(suppliers, year_start, as_of),
    )
    exp_total = 0.0
    sal_total = 0.0
    for items in merged.values():
        for it in items:
            exp_total += float(it["amount"])
            if it["name"] == "salaries":
                sal_total += float(it["amount"])

    summary = estimate_period(
        profile=profile,
        income_total=ytd_rev,
        expense_total=exp_total,
        salary_expense_total=sal_total,
        tax_reserve=float(business.tax_reserve or 0),
        vat_reserve=float(business.vat_reserve or 0),
        cash_on_hand=float(business.cash_on_hand or 0),
        ytd_turnover_value=ytd_rev,
        rolling_12m=ytd_rev,
    )
    print("\n  YTD estimate:", {
        k: summary[k] for k in (
            "income_total", "estimated_income_tax", "estimated_vat",
            "estimated_total_tax", "cash_set_aside", "still_to_set_aside", "available_cash"
        )
    })

    if profile["tax_regime"] == "small" and not profile["is_vat_payer"]:
        exp_est = round(ytd_rev * SMALL_RATE, 2) if ytd_rev <= SMALL_TURNOVER_CAP else None
        if exp_est is not None:
            # pension adds to estimated_total
            check(
                "YTD small tax estimate = 1% of YTD revenue",
                approx(summary["estimated_income_tax"], exp_est, tol=0.05),
                f"est={summary['estimated_income_tax']} expected={exp_est}",
            )
            check("YTD VAT estimate 0 for non-VAT", summary["estimated_vat"] == 0)
            # Pension is in estimated_total but must NOT inflate the set-aside gap
            sales_est = round(
                summary["estimated_income_tax"] + summary["estimated_vat"], 2
            )
            check(
                "still_to_set_aside excludes employer pension",
                approx(
                    summary["still_to_set_aside"],
                    max(0.0, sales_est - summary["cash_set_aside"]),
                    tol=0.05,
                ),
                f"gap={summary['still_to_set_aside']} sales_est={sales_est} "
                f"set_aside={summary['cash_set_aside']} "
                f"pension={summary.get('employer_pension_estimate')}",
            )
            check(
                "fully reserved sales tax -> gap ~0",
                approx(summary["still_to_set_aside"], 0.0, tol=1.0),
                f"gap={summary['still_to_set_aside']}",
            )
            check(
                "estimated_total includes pension above sales tax",
                approx(
                    summary["estimated_total_tax"],
                    sales_est + float(summary.get("employer_pension_estimate") or 0),
                    tol=0.05,
                ),
                f"total={summary['estimated_total_tax']} sales={sales_est}",
            )

    # Tax payments on 15th
    start = as_of + timedelta(days=1)
    end = start + timedelta(days=89)
    # Need forecast-like income for future months â€” use flat avg
    avg = (sum(r["revenue"] for r in rows[-30:]) / max(len(rows[-30:]), 1)) if rows else 400
    fc = [{"date": (start + timedelta(days=i)).isoformat(), "yhat": avg} for i in range(90)]
    pays = expand_tax_payments(
        profile=profile,
        daily_rows=rows,
        expenses=exps,
        start=start,
        end=end,
        income_forecast=fc,
    )
    print("\n  Tax payment dates (next 90d):")
    for d in sorted(pays):
        print("   ", d, pays[d])
    check("has tax remittance markers on 15ths", any(d.day == 15 for d in pays), f"count={len(pays)}")

    # Obligations
    obs = resolve_obligations(profile)
    codes = {o["code"] for o in obs}
    check("small obligations include turnover tax", "small_turnover_tax" in codes, str(codes))
    check("employees â†’ payroll obligation", "payroll_pit" in codes, str(codes))
    check("no VAT obligation for non-VAT demo", "vat" not in codes, str(codes))

    # Simulate LLC+VAT+draws on same YTD income (what user tested)
    print("\n=== What-if: same income under user's LLC+VAT+draws profile ===")
    llc_profile = {
        "legal_form": "llc",
        "tax_regime": "llc_estonian",
        "is_vat_payer": True,
        "has_employees": True,
        "pension_participants": True,
        "llc_distributes_profit": True,
    }
    llc_sum = estimate_period(
        profile=llc_profile,
        income_total=ytd_rev if ytd_rev > 0 else 25656.04,
        expense_total=exp_total,
        salary_expense_total=sal_total,
        tax_reserve=0,
        vat_reserve=0,
        cash_on_hand=float(business.cash_on_hand or 0),
        ytd_turnover_value=ytd_rev if ytd_rev > 0 else 25656.04,
        rolling_12m=ytd_rev if ytd_rev > 0 else 25656.04,
    )
    inc = llc_sum["income_total"]
    net = round(inc / 1.18, 2)
    vat_e = round(inc * 0.18 / 1.18, 2)
    llc_e = round(net * LLC_DRAW_SHARE_OF_NET * LLC_DISTRIBUTION_EFFECTIVE, 2)
    check(
        "LLC+VAT estimated VAT matches 18/118",
        approx(llc_sum["estimated_vat"], vat_e),
        f"{llc_sum['estimated_vat']} vs {vat_e}",
    )
    check(
        "LLC+VAT estimated draw tax matches formula",
        approx(llc_sum["estimated_income_tax"], llc_e),
        f"{llc_sum['estimated_income_tax']} vs {llc_e}",
    )
    print("  LLC+VAT YTD total tax estimate", llc_sum["estimated_total_tax"])

    # Live sale accrual
    print("\n=== Live accrual on a 100 GEL cash sale ===")
    before_t, before_v = float(business.tax_reserve or 0), float(business.vat_reserve or 0)
    from app.services.tax_accrual import accrue_income_tax
    # Use a date on/after baseline
    sale_day = max(baseline, date.today())
    part = accrue_income_tax(business, 100.0, sale_day)
    db.session.rollback()  # don't persist test sale accrual
    # re-fetch clean
    db.session.refresh(business)
    check(
        "accrue 100 GEL on IE small â†’ +1.00 tax, +0 VAT",
        approx(part.get("income_tax_accrual", 0), 1.0) and approx(part.get("vat_accrual", 0), 0.0),
        str(part),
    )


def main() -> int:
    app = create_app()
    with app.app_context():
        test_unit_math()
        user = User.query.filter_by(email=DEMO_EMAIL).first()
        if not user or not user.business:
            print("FAIL: demo user missing â€” start app with DEMO_SEED=true once")
            return 1
        repair_demo_history(user.business)
        # reload
        business = db.session.get(Business, user.business.id)
        rebuild_tax_reserves(business)
        db.session.commit()
        audit_demo(business)

        # API login smoke
        print("\n=== API login + /tax/summary ===")
        client = app.test_client()
        login = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        check("demo login", login.status_code == 200, str(login.status_code))
        token = (login.get_json() or {}).get("access_token")
        if token:
            summ = client.get(
                "/api/tax/summary?period=ytd",
                headers={"Authorization": f"Bearer {token}"},
            )
            check("GET /tax/summary", summ.status_code == 200, str(summ.status_code))
            body = summ.get_json() or {}
            print("  summary keys sample:", {k: body.get(k) for k in (
                "income_total", "estimated_total_tax", "cash_set_aside",
                "still_to_set_aside", "available_cash", "profile"
            )})
            dash = client.get(
                "/api/forecast/dashboard?horizon=90",
                headers={"Authorization": f"Bearer {token}"},
            )
            check("GET /forecast/dashboard", dash.status_code == 200, str(dash.status_code))
            dj = dash.get_json() or {}
            ts = dj.get("tax_summary") or {}
            markers = dj.get("expense_markers") or []
            tax_markers = [m for m in markers if any(
                (i.get("type") == "tax") for i in (m.get("items") or [])
            )]
            check(
                "dashboard tax_summary present",
                bool(ts),
                f"keys={list(ts.keys())[:8]}",
            )
            check(
                "dashboard includes tax expense markers",
                len(tax_markers) > 0,
                f"tax_marker_days={len(tax_markers)} total_markers={len(markers)}",
            )

        print("\n========== SUMMARY ==========")
        print(f"Passed: {len(OKS)}")
        print(f"Failed: {len(ISSUES)}")
        for i in ISSUES:
            print(" -", i)
        return 1 if ISSUES else 0


if __name__ == "__main__":
    raise SystemExit(main())

