"""Universal CSV parser for POS exports → date + revenue."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import List, Tuple

import pandas as pd


DATE_CANDIDATES = [
    "date",
    "Date",
    "DATE",
    "day",
    "Day",
    "sale_date",
    "Sale Date",
    "transaction_date",
    "თარიღი",
    "ds",
]

REVENUE_CANDIDATES = [
    "revenue",
    "Revenue",
    "amount",
    "Amount",
    "total",
    "Total",
    "sales",
    "Sales",
    "sum",
    "Sum",
    "gross",
    "Gross",
    "თანხა",
    "გაყიდვები",
    "y",
]


def _pick_column(columns, candidates) -> str | None:
    lower_map = {str(c).strip().lower(): c for c in columns}
    for cand in candidates:
        key = cand.lower()
        if key in lower_map:
            return lower_map[key]
    # fuzzy contains
    for col in columns:
        cl = str(col).strip().lower()
        for cand in candidates:
            if cand.lower() in cl:
                return col
    return None


def parse_sales_csv(text: str) -> Tuple[List[dict], List[str]]:
    """
    Returns (rows, warnings).
    rows: [{date: 'YYYY-MM-DD', revenue: float}]
    """
    warnings: List[str] = []
    # Try separators
    df = None
    for sep in [",", ";", "\t"]:
        try:
            candidate = pd.read_csv(StringIO(text), sep=sep)
            if candidate.shape[1] >= 2:
                df = candidate
                break
        except Exception:  # noqa: BLE001
            continue
    if df is None or df.empty:
        raise ValueError("Could not parse CSV. Provide at least date and revenue columns.")

    date_col = _pick_column(df.columns, DATE_CANDIDATES)
    rev_col = _pick_column(df.columns, REVENUE_CANDIDATES)

    if date_col is None or rev_col is None:
        # Fallback: first column date-like, second numeric
        if df.shape[1] < 2:
            raise ValueError("CSV must include date and revenue columns.")
        date_col = df.columns[0]
        rev_col = df.columns[1]
        warnings.append(
            f"Using columns '{date_col}' and '{rev_col}' as date/revenue."
        )

    parsed = []
    for _, row in df.iterrows():
        raw_date = row[date_col]
        raw_rev = row[rev_col]
        if pd.isna(raw_date) or pd.isna(raw_rev):
            continue
        try:
            ds = pd.to_datetime(raw_date, dayfirst=True, errors="coerce")
            if pd.isna(ds):
                continue
            revenue = float(str(raw_rev).replace(",", "").replace("₾", "").strip())
        except Exception:  # noqa: BLE001
            continue
        if revenue < 0:
            continue
        parsed.append({"date": ds.date().isoformat(), "revenue": revenue})

    if not parsed:
        raise ValueError("No valid date/revenue rows found in CSV.")

    # Aggregate duplicate dates
    agg = {}
    for item in parsed:
        agg[item["date"]] = agg.get(item["date"], 0.0) + item["revenue"]
    rows = [{"date": k, "revenue": round(v, 2)} for k, v in sorted(agg.items())]
    return rows, warnings
