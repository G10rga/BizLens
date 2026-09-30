"""Generate actionable cash-flow alerts from forecast + Georgian calendar."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List

from .georgian_calendar import events_between


def build_alerts(
    *,
    business_type: str,
    cashflow_timeline: List[dict],
    expense_markers: List[dict],
    as_of: date | None = None,
) -> List[dict]:
    as_of = as_of or date.today()
    alerts: List[dict] = []

    # Danger zone alert
    danger = next((row for row in cashflow_timeline if row["zone"] == "red"), None)
    if danger:
        danger_date = date.fromisoformat(danger["date"])
        days = (danger_date - as_of).days
        # Find nearest expense around danger
        nearby_exp = None
        for marker in expense_markers:
            md = date.fromisoformat(marker["date"])
            if abs((md - danger_date).days) <= 5:
                nearby_exp = marker
                break
        if nearby_exp:
            items = ", ".join(i["name"] for i in nearby_exp["items"])
            need = max(0.0, 500 - danger["cash_likely"])
            msg = (
                f"Your cash will drop to ₾{danger['cash_likely']:.0f} on {danger_date.isoformat()} "
                f"({days} days). Nearby expenses: {items} (₾{nearby_exp['amount']:.0f}). "
                f"Prepare about ₾{need:.0f} extra before then."
            )
            msg_ka = (
                f"თქვენი ნაღდი ფული დაეცემა ₾{danger['cash_likely']:.0f}-მდე {danger_date.isoformat()}-ს "
                f"({days} დღეში). ახლომდებარე ხარჯები: {items} (₾{nearby_exp['amount']:.0f}). "
                f"მოამზადეთ დაახლოებით ₾{need:.0f}."
            )
        else:
            msg = (
                f"Cash danger in {days} days: projected ₾{danger['cash_likely']:.0f} on "
                f"{danger_date.isoformat()}."
            )
            msg_ka = (
                f"ფულის საფრთხე {days} დღეში: პროგნოზი ₾{danger['cash_likely']:.0f} "
                f"{danger_date.isoformat()}-ს."
            )
        alerts.append(
            {
                "severity": "danger",
                "title": f"Cash Danger in {days} Days",
                "title_ka": f"ფულის საფრთხე {days} დღეში",
                "message": msg,
                "message_ka": msg_ka,
                "alert_date": danger_date,
                "amount": danger["cash_likely"],
            }
        )

    # Upcoming Georgian events
    window_end = as_of + timedelta(days=90)
    for event in events_between(as_of, window_end):
        if event["key"] == "new_year" and as_of <= event["start"] <= as_of + timedelta(days=60):
            alerts.append(
                {
                    "severity": "opportunity",
                    "title": "New Year Opportunity — Prepare Now",
                    "title_ka": "ახალი წელი — მოემზადეთ ახლა",
                    "message": (
                        "New Year is approaching. Based on Georgian seasonality, sales often surge "
                        "strongly. Ensure stock purchase cash is ready 2–3 weeks before."
                    ),
                    "message_ka": (
                        "ახალი წელი ახლოვდება. ქართული სეზონურობის მიხედვით გაყიდვები ხშირად მკვეთრად იზრდება. "
                        "მარაგის შესაძენი თანხა მოამზადეთ 2–3 კვირით ადრე."
                    ),
                    "alert_date": event["start"],
                    "amount": None,
                }
            )
        if event["key"] == "fasting" and as_of <= event["start"] <= as_of + timedelta(days=21):
            tone = (
                "expect shifts in product mix (bread/pastry up, meat/dairy down)"
                if business_type == "bakery"
                else "expect softer demand for some categories"
            )
            alerts.append(
                {
                    "severity": "warning",
                    "title": "Fasting Period Starting",
                    "title_ka": "მარხვის პერიოდი იწყება",
                    "message": (
                        f"Orthodox fasting begins around {event['start'].isoformat()}. "
                        f"For your business type, {tone}. Forecast already adjusted."
                    ),
                    "message_ka": (
                        f"მართლმადიდებლური მარხვა იწყება დაახლოებით {event['start'].isoformat()}-ს. "
                        "პროგნოზი უკვე მორგებულია."
                    ),
                    "alert_date": event["start"],
                    "amount": None,
                }
            )
        if event["key"] == "winter_slowdown" and as_of <= event["start"] <= as_of + timedelta(days=14):
            alerts.append(
                {
                    "severity": "warning",
                    "title": "Post-Holiday Slowdown Ahead",
                    "title_ka": "დღესასწაულის შემდეგი ვარდნა",
                    "message": (
                        "January–February slowdown often follows New Year peaks. "
                        "Avoid overcommitting cash right after the holiday rush."
                    ),
                    "message_ka": (
                        "იანვარ-თებერვლის ვარდნა ხშირად მოსდევს საახალწლო პიკს. "
                        "ნუ გადაიხდით ზედმეტად დღესასწაულის შემდეგ."
                    ),
                    "alert_date": event["start"],
                    "amount": None,
                }
            )
        if event["key"] == "tbilisoba" and as_of <= event["start"] <= as_of + timedelta(days=21):
            alerts.append(
                {
                    "severity": "opportunity",
                    "title": "Tbilisoba Traffic Spike",
                    "title_ka": "თბილისობა — გაყიდვების ზრდა",
                    "message": (
                        f"Tbilisoba starts around {event['start'].isoformat()}. "
                        "Hospitality and food businesses in Tbilisi often see a short demand spike."
                    ),
                    "message_ka": (
                        f"თბილისობა იწყება დაახლოებით {event['start'].isoformat()}-ს. "
                        "თბილისის კვების ბიზნესებს ხშირად მოკლე მოთხოვნის ზრდა აქვთ."
                    ),
                    "alert_date": event["start"],
                    "amount": None,
                }
            )

    # Deduplicate by title
    seen = set()
    unique = []
    for a in alerts:
        if a["title"] in seen:
            continue
        seen.add(a["title"])
        unique.append(a)
    return unique[:10]
