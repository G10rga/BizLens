"""Universal sales file parser (CSV / Excel) → date + revenue."""

from __future__ import annotations

import re
from io import BytesIO, StringIO
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

# Matches: 6/25/2023 (Sun)  or  2023-06-25 (Monday)
_WEEKDAY_SUFFIX = re.compile(
    r"\s*\(\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*\)\s*$",
    re.IGNORECASE,
)


def _pick_column(columns, candidates) -> str | None:
    lower_map = {str(c).strip().lower(): c for c in columns}
    for cand in candidates:
        key = cand.lower()
        if key in lower_map:
            return lower_map[key]
    for col in columns:
        cl = str(col).strip().lower()
        for cand in candidates:
            if cand.lower() in cl:
                return col
    return None


def _clean_date_value(raw) -> pd.Timestamp | None:
    if pd.isna(raw):
        return None
    # Excel may already give a datetime
    if hasattr(raw, "to_pydatetime"):
        return pd.Timestamp(raw)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        # Excel serial date
        try:
            return pd.to_datetime(raw, unit="D", origin="1899-12-30")
        except Exception:  # noqa: BLE001
            pass

    text = str(raw).strip()
    text = _WEEKDAY_SUFFIX.sub("", text).strip()
    # Prefer US style M/D/YYYY for this shop export
    ds = pd.to_datetime(text, errors="coerce", dayfirst=False)
    if pd.isna(ds):
        ds = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(ds):
        return None
    return pd.Timestamp(ds)


def _dataframe_from_bytes(data: bytes, filename: str = "") -> pd.DataFrame:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        return pd.read_excel(BytesIO(data))

    # Try Excel anyway if binary-looking, else CSV
    try:
        return pd.read_excel(BytesIO(data))
    except Exception:  # noqa: BLE001
        pass

    text = data.decode("utf-8-sig", errors="replace")
    for sep in [",", ";", "\t"]:
        try:
            candidate = pd.read_csv(StringIO(text), sep=sep)
            if candidate.shape[1] >= 2:
                return candidate
        except Exception:  # noqa: BLE001
            continue
    raise ValueError("Could not parse file. Upload CSV or Excel with Date and Total columns.")


def parse_sales_file(data: bytes, filename: str = "") -> Tuple[List[dict], List[str]]:
    """
    Returns (rows, warnings).
    rows: [{date: 'YYYY-MM-DD', revenue: float}]
    """
    warnings: List[str] = []
    df = _dataframe_from_bytes(data, filename)
    if df is None or df.empty:
        raise ValueError("File is empty.")

    # Drop fully empty rows
    df = df.dropna(how="all")

    date_col = _pick_column(df.columns, DATE_CANDIDATES)
    rev_col = _pick_column(df.columns, REVENUE_CANDIDATES)

    if date_col is None or rev_col is None:
        if df.shape[1] < 2:
            raise ValueError("File must include Date and Total columns.")
        date_col = df.columns[0]
        rev_col = df.columns[1]
        warnings.append(f"Using columns '{date_col}' and '{rev_col}' as date/revenue.")

    parsed = []
    skipped = 0
    for _, row in df.iterrows():
        ds = _clean_date_value(row[date_col])
        raw_rev = row[rev_col]
        if ds is None or pd.isna(raw_rev):
            skipped += 1
            continue
        try:
            revenue = float(str(raw_rev).replace(",", "").replace("₾", "").replace("$", "").strip())
        except Exception:  # noqa: BLE001
            skipped += 1
            continue
        if revenue < 0:
            continue
        parsed.append({"date": ds.date().isoformat(), "revenue": revenue})

    if not parsed:
        raise ValueError(
            "No valid Date/Total rows found. Expected dates like 6/25/2023 (Sun) and totals like 80.30."
        )

    if skipped:
        warnings.append(f"Skipped {skipped} unreadable rows.")

    agg = {}
    for item in parsed:
        agg[item["date"]] = agg.get(item["date"], 0.0) + item["revenue"]
    rows = [{"date": k, "revenue": round(v, 2)} for k, v in sorted(agg.items())]
    return rows, warnings


def parse_sales_csv(text: str) -> Tuple[List[dict], List[str]]:
    """Backward-compatible wrapper for CSV text."""
    return parse_sales_file(text.encode("utf-8-sig"), filename="upload.csv")
