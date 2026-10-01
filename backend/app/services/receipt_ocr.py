"""Lens Mode: OCR + parse Georgian / English fiscal receipts."""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import date, datetime
from typing import Any

SAMPLE_RECEIPT_TEXT = """
FISCAL RECEIPT
────────────────────────────────
Date:     15 October 2025
Time:     14:32
Items:    Bread × 2       ₾4.00
          Coffee × 1      ₾3.50
          ──────────────────────
Total:    ₾7.50
Payment:  Cash
TIN:      123456789
────────────────────────────────
"""

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "იანვარი": 1,
    "თებერვალი": 2,
    "მარტი": 3,
    "აპრილი": 4,
    "მაისი": 5,
    "ივნისი": 6,
    "ივლისი": 7,
    "აგვისტო": 8,
    "სექტემბერი": 9,
    "ოქტომბერი": 10,
    "ნოემბერი": 11,
    "დეკემბერი": 12,
}


def sample_receipt_text() -> str:
    return SAMPLE_RECEIPT_TEXT.strip()


def ocr_status() -> dict[str, Any]:
    """Which free/paid OCR backends are available right now."""
    tess_ok = _tesseract_available()
    ocr_space_key = os.getenv("OCR_SPACE_API_KEY", "helloworld").strip()
    return {
        "tesseract": tess_ok,
        "ocr_space": bool(ocr_space_key),
        "ocr_space_key_set": bool(os.getenv("OCR_SPACE_API_KEY", "").strip()),
        "openai_vision": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "preferred_order": ["tesseract", "ocr_space", "openai_vision"],
        "note": (
            "Free path: Tesseract (local) or OCR.space (cloud). "
            "Get a free OCR.space key at https://ocr.space/ocrapi — "
            "or leave unset to use the public helloworld demo key (rate-limited)."
        ),
    }


def extract_text_from_image(image_bytes: bytes, filename: str = "receipt.jpg") -> tuple[str, str]:
    """
    Returns (raw_text, engine_name).
    Free-first: Tesseract → OCR.space → optional OpenAI Vision → empty.
    """
    tess = _tesseract_extract(image_bytes)
    if tess:
        return tess, "tesseract"

    space = _ocr_space_extract(image_bytes, filename)
    if space:
        return space, "ocr_space"

    openai_text = _openai_vision_extract(image_bytes, filename)
    if openai_text:
        return openai_text, "openai_vision"

    return "", "none"


def parse_receipt_text(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {
            "receipt_date": date.today().isoformat(),
            "receipt_time": None,
            "total": None,
            "payment_method": "unknown",
            "tin": None,
            "items": [],
            "parse_confidence": 0.05,
            "warnings": ["No OCR text — enter totals manually"],
        }

    warnings: list[str] = []
    receipt_date = _parse_date(text)
    receipt_time = _parse_time(text)
    total = _parse_total(text)
    payment = _parse_payment(text)
    tin = _parse_tin(text)
    items = _parse_items(text)

    # Free OCR often drops the "Total" line — fall back to sum of items
    if total is None and items:
        total = round(sum(float(i.get("line_total") or 0) for i in items), 2)
        warnings.append("Total inferred from line items — please verify")
    elif total is not None and items:
        items_sum = round(sum(float(i.get("line_total") or 0) for i in items), 2)
        if items_sum > 0 and abs(items_sum - total) > 0.05 and items_sum > total:
            # OCR sometimes picks a line price as "total"; prefer items sum when larger
            if total <= max(float(i.get("line_total") or 0) for i in items) + 0.001:
                warnings.append(f"Total looked low ({total}); using items sum {items_sum}")
                total = items_sum

    score = 0.15
    if receipt_date:
        score += 0.25
    if receipt_time:
        score += 0.1
    if total is not None:
        score += 0.35
    if payment in {"cash", "card"}:
        score += 0.1
    if items:
        score += 0.1
    if tin:
        score += 0.05

    if total is None:
        warnings.append("Could not detect total — please enter it")
    if not receipt_date:
        receipt_date = date.today()
        warnings.append("Date missing — defaulted to today")

    return {
        "receipt_date": receipt_date.isoformat() if isinstance(receipt_date, date) else receipt_date,
        "receipt_time": receipt_time,
        "total": total,
        "payment_method": payment,
        "tin": tin,
        "items": items,
        "parse_confidence": round(min(score, 0.98), 2),
        "warnings": warnings,
    }


def parse_image(image_bytes: bytes, filename: str = "receipt.jpg") -> dict[str, Any]:
    raw, engine = extract_text_from_image(image_bytes, filename)
    parsed = parse_receipt_text(raw)
    parsed["raw_text"] = raw
    parsed["ocr_engine"] = engine
    if engine == "none":
        parsed["warnings"] = list(parsed.get("warnings") or []) + [
            "No OCR text yet — enter total manually, or set OCR_SPACE_API_KEY (free), "
            "or install Tesseract"
        ]
        parsed["parse_confidence"] = min(float(parsed.get("parse_confidence") or 0), 0.1)
    elif engine == "ocr_space":
        parsed["warnings"] = list(parsed.get("warnings") or []) + [
            "Parsed with free OCR.space — review totals before confirming"
        ]
    return parsed


def _tesseract_available() -> bool:
    try:
        import pytesseract
        from PIL import Image  # noqa: F401

        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        return False


def _ocr_space_extract(image_bytes: bytes, filename: str) -> str:
    """
    Free cloud OCR via https://ocr.space (no credit card for free tier).
    Uses OCR_SPACE_API_KEY, or the public demo key helloworld (rate-limited).
    """
    # Allow disabling: OCR_SPACE_API_KEY=off
    key = os.getenv("OCR_SPACE_API_KEY", "helloworld").strip()
    if not key or key.lower() in {"off", "false", "0", "disabled"}:
        return ""

    try:
        import urllib.error
        import urllib.parse
        import urllib.request

        mime = "image/jpeg"
        lower = (filename or "").lower()
        if lower.endswith(".png"):
            mime = "image/png"
        elif lower.endswith(".webp"):
            mime = "image/webp"
        elif lower.endswith(".gif"):
            mime = "image/gif"

        b64 = base64.b64encode(image_bytes).decode("ascii")
        # Prefer base64 endpoint — simpler than multipart without extra deps
        form = urllib.parse.urlencode(
            {
                "apikey": key,
                "language": os.getenv("OCR_SPACE_LANGUAGE", "eng"),
                "isOverlayRequired": "false",
                "OCREngine": os.getenv("OCR_SPACE_ENGINE", "2"),
                "scale": "true",
                "base64Image": f"data:{mime};base64,{b64}",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.ocr.space/parse/image",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("IsErroredOnProcessing"):
            err = data.get("ErrorMessage") or data.get("ErrorDetails") or "ocr.space error"
            if isinstance(err, list):
                err = "; ".join(str(x) for x in err)
            # Soft-fail so other engines / manual entry can continue
            return ""

        results = data.get("ParsedResults") or []
        if not results:
            return ""
        text = (results[0].get("ParsedText") or "").strip()
        return text
    except Exception:  # noqa: BLE001
        return ""


def _openai_vision_extract(image_bytes: bytes, filename: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    try:
        import urllib.error
        import urllib.request

        mime = "image/jpeg"
        lower = filename.lower()
        if lower.endswith(".png"):
            mime = "image/png"
        elif lower.endswith(".webp"):
            mime = "image/webp"
        b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all readable text from this Georgian fiscal receipt photo. "
                                "Return plain text only, preserving lines for date, time, items, total, "
                                "payment method, and TIN."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 800,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
    except Exception:  # noqa: BLE001
        return ""


def _tesseract_extract(image_bytes: bytes) -> str:
    try:
        from io import BytesIO

        import pytesseract
        from PIL import Image

        img = Image.open(BytesIO(image_bytes))
        if img.mode not in {"RGB", "L"}:
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img, lang="eng+kat")
        return (text or "").strip()
    except Exception:  # noqa: BLE001
        try:
            from io import BytesIO

            import pytesseract
            from PIL import Image

            img = Image.open(BytesIO(image_bytes))
            return pytesseract.image_to_string(img).strip()
        except Exception:  # noqa: BLE001
            return ""


def _parse_date(text: str) -> date | None:
    # 15 October 2025 / 15 ოქტომბერი 2025
    m = re.search(
        r"(\d{1,2})\s+([A-Za-zა-ჰ]+)\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2).lower())
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    for pattern, fmt in (
        (r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})", "%Y-%m-%d"),
        (r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", "%d-%m-%Y"),
    ):
        m = re.search(pattern, text)
        if not m:
            continue
        raw = m.group(1).replace("/", "-").replace(".", "-")
        parts = raw.split("-")
        try:
            if fmt == "%Y-%m-%d":
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
        except ValueError:
            continue

    # ISO-ish datetime
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return None


def _parse_time(text: str) -> str | None:
    m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b", text)
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    return f"{hh:02d}:{mm:02d}"


def _parse_total(text: str) -> float | None:
    patterns = [
        r"(?:Total|TOTAL|ჯამი|თანხა)\s*[:\-]?\s*₾?\s*([0-9]+[.,][0-9]{2})",
        r"₾\s*([0-9]+[.,][0-9]{2})\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return float(m.group(1).replace(",", "."))
    # last money-looking amount on a Total-ish line
    amounts = re.findall(r"₾?\s*([0-9]+[.,][0-9]{2})", text)
    if amounts:
        return float(amounts[-1].replace(",", "."))
    return None


def _parse_payment(text: str) -> str:
    lower = text.lower()
    if re.search(r"\b(card|visa|mastercard|ბარათი|card payment)\b", lower):
        return "card"
    if re.search(r"\b(cash|ნაღდი|ნაღდი ანგარიშსწორება)\b", lower):
        return "cash"
    return "unknown"


def _parse_tin(text: str) -> str | None:
    m = re.search(r"(?:TIN|საიდენტიფიკაციო|პ/ნ|ID)\s*[:\-]?\s*(\d{9,11})", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{9})\b", text)
    return m.group(1) if m else None


def _parse_items(text: str) -> list[dict]:
    items: list[dict] = []
    # Bread × 2  ₾4.00  or  Items: Bread x 2  4.00
    pattern = re.compile(
        r"(?:Items?\s*:\s*)?([A-Za-zა-ჰ][A-Za-zა-ჰ0-9 \-]{0,40}?)\s*[×xXх]\s*(\d+)\s+₾?\s*([0-9]+[.,][0-9]{2})",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        name = m.group(1).strip(" :-")
        if re.search(r"total|ჯამი|payment|date|time|tin|fiscal|items?", name, re.I):
            continue
        qty = int(m.group(2))
        line_total = float(m.group(3).replace(",", "."))
        unit = round(line_total / qty, 2) if qty else line_total
        items.append(
            {
                "product_name": name,
                "quantity": qty,
                "unit_price": unit,
                "line_total": line_total,
            }
        )
    return items

def combine_sold_at(receipt_date: date, receipt_time: str | None) -> datetime:
    if receipt_time:
        try:
            hh, mm = [int(x) for x in receipt_time.split(":")[:2]]
            return datetime(receipt_date.year, receipt_date.month, receipt_date.day, hh, mm)
        except ValueError:
            pass
    return datetime(receipt_date.year, receipt_date.month, receipt_date.day, 12, 0)
