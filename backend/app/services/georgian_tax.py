"""Georgian tax estimates for BizLens cash-flow reserves.

Rates and thresholds reflect published Georgian Tax Code practice for small
businesses (IE micro/small/general, LLC Estonian-model CIT, VAT, payroll).
Estimates are for cash planning only — not tax, accounting, or legal advice.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

# --- Published rates / thresholds (GEL) -------------------------------------

MICRO_TURNOVER_CAP = 30_000.0
SMALL_TURNOVER_CAP = 500_000.0
VAT_ROLLING_THRESHOLD = 100_000.0

SMALL_RATE = 0.01
SMALL_OVER_CAP_RATE = 0.03
GENERAL_PIT_RATE = 0.20
VAT_RATE = 0.18
VAT_DIVISOR = 1.0 + VAT_RATE  # VAT-inclusive price → net + VAT

LLC_CIT_RATE = 0.15  # on distributed profit (gross-up base)
LLC_DIVIDEND_RATE = 0.05  # withholding on dividend to individual
# Cash leaving company: distribute D net of CIT → owner receives D*(1-0.05);
# CIT on distribution is computed so 15 tax accompanies 85 dividend → effective
# tax on pre-distribution cash ≈ 1 - 0.85*0.95 = 0.1925
LLC_DISTRIBUTION_EFFECTIVE = 1.0 - (1.0 - LLC_CIT_RATE) * (1.0 - LLC_DIVIDEND_RATE)

PAYROLL_PIT_RATE = 0.20
PENSION_EMPLOYEE_RATE = 0.02
PENSION_EMPLOYER_RATE = 0.02

LEGAL_FORMS = frozenset({"ie", "llc"})
TAX_REGIMES = frozenset({"micro", "small", "general", "llc_estonian"})
TURNOVER_BANDS = frozenset({"under_30k", "30k_100k", "100k_500k", "over_500k", "unsure"})

OBLIGATION_COPY = {
    "micro_exempt": {
        "en": {
            "title": "Micro business — 0% income tax",
            "detail": "Annual turnover up to ₾30,000; no employees; cannot register for VAT.",
        },
        "ka": {
            "title": "მიკრო ბიზნესი — 0% საშემოსავლო",
            "detail": "წლიური ბრუნვა ₾30,000-მდე; თანამშრომლები დაუშვებელია; დღგ-ზე რეგისტრაცია შეუძლებელია.",
        },
    },
    "small_turnover_tax": {
        "en": {
            "title": "Small business turnover tax (1%)",
            "detail": "1% of gross turnover up to ₾500,000/year; 3% from the month you exceed the cap. Pay by the 15th of the next month.",
        },
        "ka": {
            "title": "მცირე ბიზნესის ბრუნვის გადასახადი (1%)",
            "detail": "ბრუნვის 1% წელიწადში ₾500,000-მდე; ლიმიტის გადაჭარბების თვიდან — 3%. გადახდა მომდევნო თვის 15 რიცხვამდე.",
        },
    },
    "pit_profit": {
        "en": {
            "title": "Personal income tax on profit (20%)",
            "detail": "20% on revenue minus deductible business expenses (general IE regime).",
        },
        "ka": {
            "title": "საშემოსავლო გადასახადი მოგებაზე (20%)",
            "detail": "შემოსავლისა და გამოქვითვადი ხარჯების სხვაობის 20% (ზოგადი რეჟიმი ინდმეწარმისთვის).",
        },
    },
    "llc_distribution": {
        "en": {
            "title": "LLC profit distribution tax (~19.25%)",
            "detail": "Retained profit is untaxed. When profit is distributed: 15% CIT + 5% dividend withholding.",
        },
        "ka": {
            "title": "შპს მოგების განაწილების გადასახადი (~19.25%)",
            "detail": "დატოვებული მოგება არ იბეგრება. განაწილებისას: 15% მოგების გადასახადი + 5% დივიდენდი.",
        },
    },
    "llc_retained": {
        "en": {
            "title": "LLC — no CIT while profit is retained",
            "detail": "Estonian model: corporate tax arises only when profit is distributed or treated as distributed.",
        },
        "ka": {
            "title": "შპს — მოგების გადასახადი მხოლოდ განაწილებისას",
            "detail": "ესტონური მოდელი: გადასახადი წარმოიშობა მხოლოდ მოგების განაწილებისას.",
        },
    },
    "vat": {
        "en": {
            "title": "VAT (18%)",
            "detail": "Mandatory once taxable turnover exceeds ₾100,000 in any rolling 12 months. VAT registration ends Small Business Status.",
        },
        "ka": {
            "title": "დღგ (18%)",
            "detail": "სავალდებულოა, როცა დასაბეგრი ბრუნვა ნებისმიერ 12 თვეში აღემატება ₾100,000-ს. დღგ-ზე რეგისტრაცია წყვეტს მცირე ბიზნესის სტატუსს.",
        },
    },
    "payroll_pit": {
        "en": {
            "title": "Payroll income tax (20%)",
            "detail": "Withhold 20% PIT from employee salaries and remit monthly.",
        },
        "ka": {
            "title": "ხელფასის საშემოსავლო (20%)",
            "detail": "თანამშრომლის ხელფასიდან 20% იკავება და ყოველთვიურად ირიცხება.",
        },
    },
    "payroll_pension_employer": {
        "en": {
            "title": "Employer pension contribution (2%)",
            "detail": "2% employer + 2% employee funded pension for Georgian citizens and permanent residents.",
        },
        "ka": {
            "title": "დამსაქმებლის საპენსიო შენატანი (2%)",
            "detail": "დაფინანსებული საპენსიო: 2% დამსაქმებელი + 2% დასაქმებული (მოქალაქეები / მუდმივი რეზიდენტები).",
        },
    },
    "monthly_filing": {
        "en": {
            "title": "Monthly tax filing",
            "detail": "File and pay applicable turnover / VAT / payroll declarations (typically by the 15th).",
        },
        "ka": {
            "title": "ყოველთვიური დეკლარაცია",
            "detail": "ბრუნვის / დღგ / ხელფასის დეკლარაციები (ჩვეულებრივ 15 რიცხვამდე).",
        },
    },
}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def normalize_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize user/API payload into a canonical tax profile dict."""
    legal_form = (data.get("legal_form") or "").strip().lower()
    tax_regime = (data.get("tax_regime") or "").strip().lower()
    vat_raw = data.get("is_vat_payer")
    # Allow "unsure" as None for recommendation path
    if isinstance(vat_raw, str) and vat_raw.strip().lower() in {"unsure", ""}:
        is_vat_payer = None
    else:
        is_vat_payer = _as_bool(vat_raw, False) if vat_raw is not None else None

    return {
        "legal_form": legal_form,
        "tax_regime": tax_regime,
        "is_vat_payer": is_vat_payer,
        "has_employees": _as_bool(data.get("has_employees"), False),
        "pension_participants": _as_bool(data.get("pension_participants"), True),
        "llc_distributes_profit": _as_bool(data.get("llc_distributes_profit"), False),
        "approx_annual_turnover": data.get("approx_annual_turnover"),
        "turnover_band": (data.get("turnover_band") or "").strip().lower() or None,
    }


def band_to_turnover(band: Optional[str]) -> Optional[float]:
    mapping = {
        "under_30k": 25_000.0,
        "30k_100k": 65_000.0,
        "100k_500k": 250_000.0,
        "over_500k": 600_000.0,
    }
    return mapping.get(band or "")


def recommend_regime(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest legal/tax fields when the user is unsure."""
    p = normalize_profile(profile)
    legal = p["legal_form"] if p["legal_form"] in LEGAL_FORMS else "ie"
    has_employees = bool(p["has_employees"])
    turnover = p["approx_annual_turnover"]
    if turnover is None:
        turnover = band_to_turnover(p.get("turnover_band"))

    is_vat = p["is_vat_payer"]
    warnings: List[str] = []

    if legal == "llc":
        regime = "llc_estonian"
        if is_vat is None and turnover is not None and turnover >= VAT_ROLLING_THRESHOLD:
            is_vat = True
            warnings.append("vat_threshold_likely")
        elif is_vat is None:
            is_vat = False
        return {
            "legal_form": "llc",
            "tax_regime": regime,
            "is_vat_payer": bool(is_vat),
            "has_employees": has_employees,
            "warnings": warnings,
            "reason": "llc_estonian",
        }

    # IE path
    if is_vat is True or (turnover is not None and turnover >= VAT_ROLLING_THRESHOLD):
        regime = "general"
        is_vat = True
        if turnover is not None and turnover >= VAT_ROLLING_THRESHOLD:
            warnings.append("vat_mandatory")
        warnings.append("small_incompatible_with_vat")
    elif has_employees:
        # Micro forbids employees
        if turnover is not None and turnover <= MICRO_TURNOVER_CAP:
            warnings.append("micro_forbids_employees")
        regime = "small" if (turnover is None or turnover <= SMALL_TURNOVER_CAP) else "general"
        is_vat = False
    elif turnover is not None and turnover <= MICRO_TURNOVER_CAP:
        regime = "micro"
        is_vat = False
    elif turnover is None or turnover <= SMALL_TURNOVER_CAP:
        regime = "small"
        is_vat = False
    else:
        regime = "general"
        is_vat = True
        warnings.append("over_small_cap")

    return {
        "legal_form": "ie",
        "tax_regime": regime,
        "is_vat_payer": bool(is_vat),
        "has_employees": has_employees,
        "warnings": warnings,
        "reason": regime,
    }


def validate_profile(data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str], List[str]]:
    """
    Validate and coerce a tax profile.
    Returns (normalized_ready_profile | None, errors, warnings).
    """
    p = normalize_profile(data)
    errors: List[str] = []
    warnings: List[str] = []

    if p["legal_form"] not in LEGAL_FORMS:
        errors.append("legal_form_required")
    if p["tax_regime"] not in TAX_REGIMES:
        errors.append("tax_regime_required")
    if p["is_vat_payer"] is None:
        errors.append("vat_status_required")

    if errors:
        return None, errors, warnings

    legal = p["legal_form"]
    regime = p["tax_regime"]
    is_vat = bool(p["is_vat_payer"])
    has_employees = bool(p["has_employees"])

    if legal == "llc":
        if regime != "llc_estonian":
            regime = "llc_estonian"
            warnings.append("llc_regime_forced")
        if regime == "micro" or regime == "small":
            errors.append("llc_cannot_use_ie_status")
    else:
        if regime == "llc_estonian":
            errors.append("ie_cannot_use_llc_regime")

    if regime == "micro":
        if has_employees:
            errors.append("micro_forbids_employees")
        if is_vat:
            errors.append("micro_forbids_vat")
        if legal != "ie":
            errors.append("micro_ie_only")

    if regime == "small":
        if legal != "ie":
            errors.append("small_ie_only")
        if is_vat:
            errors.append("small_incompatible_with_vat")

    if is_vat and regime in {"micro", "small"}:
        errors.append("vat_ends_special_status")

    if errors:
        return None, errors, warnings

    ready = {
        "legal_form": legal,
        "tax_regime": regime,
        "is_vat_payer": is_vat,
        "has_employees": has_employees,
        "pension_participants": bool(p["pension_participants"]),
        "llc_distributes_profit": bool(p["llc_distributes_profit"]) if legal == "llc" else False,
    }
    return ready, [], warnings


def resolve_obligations(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List applicable tax liabilities for the profile."""
    p = normalize_profile(profile)
    regime = p["tax_regime"]
    legal = p["legal_form"]
    is_vat = bool(p["is_vat_payer"])
    has_employees = bool(p["has_employees"])
    distributes = bool(p["llc_distributes_profit"])
    pension = bool(p["pension_participants"])

    codes: List[str] = []
    if regime == "micro":
        codes.append("micro_exempt")
    elif regime == "small":
        codes.append("small_turnover_tax")
        codes.append("monthly_filing")
    elif regime == "general":
        codes.append("pit_profit")
        codes.append("monthly_filing")
    elif regime == "llc_estonian" or legal == "llc":
        if distributes:
            codes.append("llc_distribution")
        else:
            codes.append("llc_retained")
        codes.append("monthly_filing")

    if is_vat:
        codes.append("vat")

    if has_employees:
        codes.append("payroll_pit")
        if pension:
            codes.append("payroll_pension_employer")

    out = []
    for code in codes:
        copy = OBLIGATION_COPY.get(code, {})
        out.append(
            {
                "code": code,
                "title_en": copy.get("en", {}).get("title", code),
                "title_ka": copy.get("ka", {}).get("title", code),
                "detail_en": copy.get("en", {}).get("detail", ""),
                "detail_ka": copy.get("ka", {}).get("detail", ""),
            }
        )
    return out


def profile_from_business(business) -> Dict[str, Any]:
    return {
        "legal_form": getattr(business, "legal_form", None) or "ie",
        "tax_regime": getattr(business, "tax_regime", None) or "small",
        "is_vat_payer": bool(getattr(business, "is_vat_payer", False)),
        "has_employees": bool(getattr(business, "has_employees", False)),
        "pension_participants": bool(getattr(business, "pension_participants", True)),
        "llc_distributes_profit": bool(getattr(business, "llc_distributes_profit", False)),
    }


def _vat_from_inclusive(amount: float) -> float:
    """Extract VAT portion from a VAT-inclusive price."""
    if amount <= 0:
        return 0.0
    return round(amount * VAT_RATE / VAT_DIVISOR, 2)


def _net_from_inclusive(amount: float) -> float:
    if amount <= 0:
        return 0.0
    return round(amount / VAT_DIVISOR, 2)


def small_business_rate(ytd_turnover_before: float, amount: float) -> float:
    """Rate applicable to this sale given YTD turnover before the sale."""
    if ytd_turnover_before >= SMALL_TURNOVER_CAP:
        return SMALL_OVER_CAP_RATE
    if ytd_turnover_before + amount > SMALL_TURNOVER_CAP:
        # Month of exceedance: Tax Code applies 3% from that month — for a single
        # sale estimate, tax the portion over the cap at 3% and the rest at 1%.
        return None  # signal split handling
    return SMALL_RATE


def tax_on_income(
    amount: float,
    ytd_turnover_before: float,
    profile: Dict[str, Any],
    *,
    estimated_margin: float = 0.25,
) -> Dict[str, float]:
    """
    Accrual for one income event.
    Returns income_tax_accrual and vat_accrual (both >= 0).
    """
    amount = float(amount or 0)
    if amount <= 0:
        return {"income_tax_accrual": 0.0, "vat_accrual": 0.0, "taxable_turnover": 0.0}

    p = normalize_profile(profile)
    regime = p["tax_regime"]
    is_vat = bool(p["is_vat_payer"])

    vat_accrual = _vat_from_inclusive(amount) if is_vat else 0.0
    # For VAT payers, income-tax base is net of VAT; special IE statuses are not VAT payers.
    taxable_turnover = _net_from_inclusive(amount) if is_vat else amount

    income_tax = 0.0
    if regime == "micro":
        income_tax = 0.0
    elif regime == "small":
        rate = small_business_rate(ytd_turnover_before, taxable_turnover)
        if rate is None:
            room = max(0.0, SMALL_TURNOVER_CAP - ytd_turnover_before)
            over = max(0.0, taxable_turnover - room)
            income_tax = round(room * SMALL_RATE + over * SMALL_OVER_CAP_RATE, 2)
        else:
            income_tax = round(taxable_turnover * rate, 2)
    elif regime == "general":
        # Approximate profit as margin * net revenue (expenses tracked separately in period estimate)
        income_tax = round(taxable_turnover * max(0.0, min(estimated_margin, 1.0)) * GENERAL_PIT_RATE, 2)
    elif regime == "llc_estonian":
        if p["llc_distributes_profit"]:
            income_tax = round(
                taxable_turnover * max(0.0, min(estimated_margin, 1.0)) * LLC_DISTRIBUTION_EFFECTIVE,
                2,
            )
        else:
            income_tax = 0.0

    return {
        "income_tax_accrual": round(income_tax, 2),
        "vat_accrual": round(vat_accrual, 2),
        "taxable_turnover": round(taxable_turnover, 2),
    }


def accrue_reserves(business, amount: float, sale_date: date, ytd_turnover_before: float) -> Dict[str, float]:
    """Mutate business tax_reserve / vat_reserve for a new income amount."""
    if not getattr(business, "tax_profile_complete", False):
        return {"income_tax_accrual": 0.0, "vat_accrual": 0.0}

    profile = profile_from_business(business)
    result = tax_on_income(amount, ytd_turnover_before, profile)
    business.tax_reserve = round(float(business.tax_reserve or 0) + result["income_tax_accrual"], 2)
    business.vat_reserve = round(float(business.vat_reserve or 0) + result["vat_accrual"], 2)
    return result


def ytd_turnover(daily_rows: List[dict], as_of: Optional[date] = None) -> float:
    """Sum revenue from Jan 1 of as_of.year through as_of (inclusive)."""
    as_of = as_of or date.today()
    start = date(as_of.year, 1, 1)
    total = 0.0
    for row in daily_rows:
        d = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
        if start <= d <= as_of:
            total += float(row.get("revenue") or 0)
    return round(total, 2)


def rolling_12m_turnover(daily_rows: List[dict], as_of: Optional[date] = None) -> float:
    as_of = as_of or date.today()
    start = as_of - timedelta(days=364)
    total = 0.0
    for row in daily_rows:
        d = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
        if start <= d <= as_of:
            total += float(row.get("revenue") or 0)
    return round(total, 2)


def estimate_period(
    *,
    profile: Dict[str, Any],
    income_total: float,
    expense_total: float,
    salary_expense_total: float = 0.0,
    tax_reserve: float = 0.0,
    vat_reserve: float = 0.0,
    cash_on_hand: float = 0.0,
    ytd_turnover_value: float = 0.0,
    rolling_12m: float = 0.0,
) -> Dict[str, Any]:
    """Period summary for dashboard / tax summary API."""
    p = normalize_profile(profile)
    regime = p["tax_regime"]
    is_vat = bool(p["is_vat_payer"])

    net_income = _net_from_inclusive(income_total) if is_vat else income_total
    estimated_income_tax = 0.0

    if regime == "micro":
        estimated_income_tax = 0.0
    elif regime == "small":
        if ytd_turnover_value <= SMALL_TURNOVER_CAP:
            estimated_income_tax = round(net_income * SMALL_RATE, 2)
        else:
            # Rough: 1% up to cap share of period + 3% on rest — use YTD position
            estimated_income_tax = round(net_income * SMALL_OVER_CAP_RATE, 2)
    elif regime == "general":
        profit = max(0.0, net_income - expense_total)
        estimated_income_tax = round(profit * GENERAL_PIT_RATE, 2)
    elif regime == "llc_estonian" and p["llc_distributes_profit"]:
        profit = max(0.0, net_income - expense_total)
        estimated_income_tax = round(profit * LLC_DISTRIBUTION_EFFECTIVE, 2)

    estimated_vat = _vat_from_inclusive(income_total) if is_vat else 0.0

    employer_pension = 0.0
    if p["has_employees"] and p["pension_participants"] and salary_expense_total > 0:
        employer_pension = round(salary_expense_total * PENSION_EMPLOYER_RATE, 2)

    total_reserve = round(float(tax_reserve or 0) + float(vat_reserve or 0), 2)
    available = round(float(cash_on_hand or 0) - total_reserve, 2)

    warnings = []
    if not is_vat and rolling_12m >= VAT_ROLLING_THRESHOLD * 0.9:
        warnings.append("approaching_vat_threshold")
    if regime == "small" and ytd_turnover_value >= SMALL_TURNOVER_CAP * 0.9:
        warnings.append("approaching_small_cap")

    return {
        "income_total": round(income_total, 2),
        "expense_total": round(expense_total, 2),
        "salary_expense_total": round(salary_expense_total, 2),
        "estimated_income_tax": estimated_income_tax,
        "estimated_vat": estimated_vat,
        "employer_pension_estimate": employer_pension,
        "tax_reserve": round(float(tax_reserve or 0), 2),
        "vat_reserve": round(float(vat_reserve or 0), 2),
        "total_tax_reserve": total_reserve,
        "cash_on_hand": round(float(cash_on_hand or 0), 2),
        "available_cash": available,
        "ytd_turnover": round(ytd_turnover_value, 2),
        "rolling_12m_turnover": round(rolling_12m, 2),
        "vat_threshold": VAT_ROLLING_THRESHOLD,
        "small_cap": SMALL_TURNOVER_CAP,
        "micro_cap": MICRO_TURNOVER_CAP,
        "obligations": resolve_obligations(p),
        "warnings": warnings,
        "disclaimer_en": "Estimates use published Georgian rates and your profile — not tax advice.",
        "disclaimer_ka": "შეფასებები ეფუძნება გამოქვეყნებულ ქართულ განაკვეთებს და თქვენს პროფილს — ეს არ არის საგადასახადო კონსულტაცია.",
    }


def _month_bounds(year: int, month: int) -> Tuple[date, date]:
    last = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def _prev_month(d: date) -> Tuple[int, int]:
    if d.month == 1:
        return d.year - 1, 12
    return d.year, d.month - 1


def expand_tax_payments(
    *,
    profile: Dict[str, Any],
    daily_rows: List[dict],
    expenses: List[dict],
    start: date,
    end: date,
) -> Dict[date, List[dict]]:
    """
    Map payment dates (15th) → estimated tax remittances for prior calendar month.
    Used by cash-flow projection like fixed expenses.
    """
    p = normalize_profile(profile)
    if p["tax_regime"] not in TAX_REGIMES and p["legal_form"] not in LEGAL_FORMS:
        return {}

    by_day: Dict[date, List[dict]] = {}

    # Walk each month whose 15th falls in [start, end]
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        pay_day = date(cursor.year, cursor.month, min(15, monthrange(cursor.year, cursor.month)[1]))
        if start <= pay_day <= end:
            py, pm = _prev_month(pay_day)
            m_start, m_end = _month_bounds(py, pm)
            month_income = 0.0
            for row in daily_rows:
                d = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
                if m_start <= d <= m_end:
                    month_income += float(row.get("revenue") or 0)

            # YTD before this month for small-business rate
            ytd_before = 0.0
            year_start = date(py, 1, 1)
            for row in daily_rows:
                d = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
                if year_start <= d < m_start:
                    ytd_before += float(row.get("revenue") or 0)

            items: List[dict] = []
            accrual = tax_on_income(month_income, ytd_before, p)
            if accrual["income_tax_accrual"] > 0:
                label = {
                    "small": "small_business_tax",
                    "general": "income_tax",
                    "llc_estonian": "llc_distribution_tax",
                    "micro": "income_tax",
                }.get(p["tax_regime"], "income_tax")
                items.append(
                    {
                        "type": "tax",
                        "name": label,
                        "amount": accrual["income_tax_accrual"],
                    }
                )
            if accrual["vat_accrual"] > 0:
                items.append(
                    {
                        "type": "tax",
                        "name": "vat",
                        "amount": accrual["vat_accrual"],
                    }
                )

            # Employer pension on salary fixed expenses due in prior month
            if p["has_employees"] and p["pension_participants"]:
                salary = 0.0
                for exp in expenses:
                    if (exp.get("name") or "").lower() == "salaries":
                        salary += float(exp.get("amount") or 0)
                if salary > 0:
                    items.append(
                        {
                            "type": "tax",
                            "name": "employer_pension",
                            "amount": round(salary * PENSION_EMPLOYER_RATE, 2),
                        }
                    )

            if items:
                by_day.setdefault(pay_day, []).extend(items)

        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    return by_day


def available_cash(business) -> float:
    cash = float(getattr(business, "cash_on_hand", 0) or 0)
    tax_r = float(getattr(business, "tax_reserve", 0) or 0)
    vat_r = float(getattr(business, "vat_reserve", 0) or 0)
    return round(cash - tax_r - vat_r, 2)
