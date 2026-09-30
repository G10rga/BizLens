"""Georgian Intelligence Layer — holidays and cultural seasonality for forecasts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

# Business-type multipliers applied around event windows.
# Values > 1 boost expected revenue; < 1 dampen it.
BUSINESS_TYPE_EVENT_MULTIPLIERS = {
    "bakery": {
        "new_year": 1.8,
        "orthodox_christmas": 1.35,
        "orthodox_easter": 1.5,
        "fasting": 1.2,  # bread/lobiani up during fasting
        "tbilisoba": 1.25,
        "tourism_season": 1.1,
        "winter_slowdown": 0.7,
        "school_start": 1.05,
    },
    "restaurant": {
        "new_year": 1.6,
        "orthodox_christmas": 1.2,
        "orthodox_easter": 1.4,
        "fasting": 0.75,
        "tbilisoba": 1.4,
        "tourism_season": 1.35,
        "winter_slowdown": 0.75,
        "school_start": 1.0,
    },
    "retail": {
        "new_year": 1.7,
        "orthodox_christmas": 1.3,
        "orthodox_easter": 1.2,
        "fasting": 0.95,
        "tbilisoba": 1.15,
        "tourism_season": 1.2,
        "winter_slowdown": 0.7,
        "school_start": 1.25,
    },
    "pharmacy": {
        "new_year": 1.05,
        "orthodox_christmas": 1.0,
        "orthodox_easter": 1.0,
        "fasting": 1.0,
        "tbilisoba": 1.0,
        "tourism_season": 1.05,
        "winter_slowdown": 1.1,
        "school_start": 1.1,
    },
    "salon": {
        "new_year": 1.45,
        "orthodox_christmas": 1.15,
        "orthodox_easter": 1.25,
        "fasting": 0.9,
        "tbilisoba": 1.1,
        "tourism_season": 1.15,
        "winter_slowdown": 0.85,
        "school_start": 1.05,
    },
    "other": {
        "new_year": 1.3,
        "orthodox_christmas": 1.15,
        "orthodox_easter": 1.2,
        "fasting": 0.9,
        "tbilisoba": 1.1,
        "tourism_season": 1.15,
        "winter_slowdown": 0.8,
        "school_start": 1.1,
    },
}


def _orthodox_easter(year: int) -> date:
    """Meeus Julian algorithm for Orthodox Easter (Gregorian result)."""
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = ((d + e + 114) % 31) + 1
    julian = date(year, month, day)
    # Convert Julian Easter to Gregorian (+13 days in 20th/21st century)
    return julian + timedelta(days=13)


def georgian_events_for_year(year: int) -> List[dict]:
    easter = _orthodox_easter(year)
    # Approx Great Lent: 48 days before Easter (includes Holy Week)
    lent_start = easter - timedelta(days=48)
    return [
        {
            "key": "new_year",
            "name": "New Year",
            "name_ka": "ახალი წელი",
            "start": date(year, 1, 1),
            "end": date(year, 1, 2),
            "prep_days": 21,
            "direction": "up",
        },
        {
            "key": "orthodox_christmas",
            "name": "Orthodox Christmas",
            "name_ka": "შობა",
            "start": date(year, 1, 7),
            "end": date(year, 1, 7),
            "prep_days": 7,
            "direction": "up",
        },
        {
            "key": "winter_slowdown",
            "name": "Post-New Year Slowdown",
            "name_ka": "საახალწლო შემცირება",
            "start": date(year, 1, 10),
            "end": date(year, 2, 15),
            "prep_days": 0,
            "direction": "down",
        },
        {
            "key": "fasting",
            "name": "Great Lent / Fasting",
            "name_ka": "დიდი მარხვა",
            "start": lent_start,
            "end": easter - timedelta(days=1),
            "prep_days": 3,
            "direction": "mixed",
        },
        {
            "key": "orthodox_easter",
            "name": "Orthodox Easter",
            "name_ka": "აღდგომა",
            "start": easter,
            "end": easter + timedelta(days=1),
            "prep_days": 7,
            "direction": "up",
        },
        {
            "key": "independence_day",
            "name": "Independence Day",
            "name_ka": "დამოუკიდებლობის დღე",
            "start": date(year, 5, 26),
            "end": date(year, 5, 26),
            "prep_days": 2,
            "direction": "up",
        },
        {
            "key": "tourism_season",
            "name": "Tourist Season",
            "name_ka": "ტურისტული სეზონი",
            "start": date(year, 6, 1),
            "end": date(year, 9, 15),
            "prep_days": 0,
            "direction": "up",
        },
        {
            "key": "mariamoba",
            "name": "Mariamoba",
            "name_ka": "მარიამობა",
            "start": date(year, 8, 28),
            "end": date(year, 8, 28),
            "prep_days": 3,
            "direction": "up",
        },
        {
            "key": "school_start",
            "name": "School Year Start",
            "name_ka": "სასკოლო წლის დასაწყისი",
            "start": date(year, 9, 1),
            "end": date(year, 9, 15),
            "prep_days": 10,
            "direction": "up",
        },
        {
            "key": "tbilisoba",
            "name": "Tbilisoba",
            "name_ka": "თბილისობა",
            "start": date(year, 10, 4),  # approx first weekend of October
            "end": date(year, 10, 6),
            "prep_days": 3,
            "direction": "up",
        },
        {
            "key": "giorgoba",
            "name": "Giorgoba",
            "name_ka": "გიორგობა",
            "start": date(year, 11, 23),
            "end": date(year, 11, 23),
            "prep_days": 3,
            "direction": "up",
        },
    ]


def events_between(start: date, end: date) -> List[dict]:
    years = range(start.year - 1, end.year + 2)
    out = []
    for y in years:
        for event in georgian_events_for_year(y):
            if event["end"] < start or event["start"] > end:
                continue
            out.append(event)
    return out


def holiday_markers(start: date, end: date) -> List[dict]:
    """Compact markers for dashboard vertical lines."""
    markers = []
    for event in events_between(start, end):
        if event["key"] in {
            "new_year",
            "orthodox_christmas",
            "orthodox_easter",
            "fasting",
            "tbilisoba",
            "giorgoba",
            "mariamoba",
            "independence_day",
            "school_start",
            "winter_slowdown",
        }:
            markers.append(
                {
                    "key": event["key"],
                    "date": event["start"].isoformat(),
                    "end": event["end"].isoformat(),
                    "name": event["name"],
                    "name_ka": event["name_ka"],
                    "direction": event["direction"],
                }
            )
    return markers


def daily_seasonality_factor(d: date, business_type: str) -> float:
    """Return a multiplicative factor for a given day based on Georgian events."""
    multipliers = BUSINESS_TYPE_EVENT_MULTIPLIERS.get(
        business_type, BUSINESS_TYPE_EVENT_MULTIPLIERS["other"]
    )
    factor = 1.0
    for event in georgian_events_for_year(d.year):
        key = event["key"]
        if key not in multipliers:
            # map close keys
            if key == "independence_day":
                mult = 1.1
            elif key in {"mariamoba", "giorgoba"}:
                mult = multipliers.get("orthodox_christmas", 1.1)
            else:
                continue
        else:
            mult = multipliers[key]

        window_start = event["start"] - timedelta(days=event.get("prep_days", 0))
        window_end = event["end"]
        if window_start <= d <= window_end:
            # Blend toward event multiplier (don't stack explosively)
            factor *= mult
    # Keep within sane bounds
    return max(0.4, min(factor, 2.5))


def prophet_holiday_frame(years: List[int]):
    """Build a Prophet-compatible holidays DataFrame."""
    import pandas as pd

    rows = []
    for y in years:
        for event in georgian_events_for_year(y):
            rows.append(
                {
                    "holiday": event["key"],
                    "ds": event["start"],
                    "lower_window": -event.get("prep_days", 0),
                    "upper_window": (event["end"] - event["start"]).days,
                }
            )
    return pd.DataFrame(rows)


def build_georgian_regressor_series(dates, business_type: str):
    """Continuous regressor = daily seasonality factor for Prophet."""
    import pandas as pd

    return pd.Series([daily_seasonality_factor(d.date() if hasattr(d, "date") else d, business_type) for d in dates])
