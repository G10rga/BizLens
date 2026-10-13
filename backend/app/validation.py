import re
from decimal import Decimal, InvalidOperation

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_EXTRA = set(" -'\u2019")


def _is_letters_name(value: str) -> bool:
    return all(ch.isalpha() or ch in NAME_EXTRA for ch in value)


def parse_money(value, *, min_value: float = 0, allow_empty: bool = False):
    if value is None or str(value).strip() == "":
        if allow_empty:
            return None
        raise ValueError("Enter a number of 0 or more, with up to 2 decimals")
    raw = str(value).strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", raw):
        raise ValueError("Enter a number of 0 or more, with up to 2 decimals")
    try:
        amount = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("Enter a number of 0 or more, with up to 2 decimals") from exc
    if amount < Decimal(str(min_value)):
        raise ValueError("Enter a number of 0 or more, with up to 2 decimals")
    return float(amount)


def validate_register(data: dict) -> str | None:
    name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return "Name is required"
    if not 2 <= len(name) <= 50:
        return "Name must be 2–50 characters"
    if not _is_letters_name(name):
        return "Name may contain letters, spaces, hyphens, and apostrophes only"

    if not email:
        return "Email is required"
    if len(email) > 254 or not EMAIL_RE.match(email):
        return "Enter a valid email address"

    if not 8 <= len(password) <= 128:
        return "Password must be 8–128 characters"
    if not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password):
        return "Password must include uppercase, lowercase, and a digit"
    return None


def validate_business_name(name: str) -> str | None:
    value = (name or "").strip()
    if not value:
        return "Business name is required"
    if not 2 <= len(value) <= 80:
        return "Business name must be 2–80 characters"
    return None


def validate_due_day(value) -> int:
    try:
        day = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Payment day must be a whole number from 1 to 31") from exc
    if not 1 <= day <= 31:
        raise ValueError("Payment day must be a whole number from 1 to 31")
    return day
