from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..services.georgian_tax import resolve_obligations, validate_profile
from ..services.tax_accrual import rebuild_tax_reserves
from .helpers import current_user, require_business
from .onboarding import ERROR_MESSAGES, _apply_tax_profile

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("")
@jwt_required()
def get_settings():
    user = current_user()
    payload = {"user": user.to_dict()}
    if user.business:
        payload["business"] = user.business.to_dict()
        if user.business.tax_profile_complete:
            payload["obligations"] = resolve_obligations(
                {
                    "legal_form": user.business.legal_form,
                    "tax_regime": user.business.tax_regime,
                    "is_vat_payer": user.business.is_vat_payer,
                    "has_employees": user.business.has_employees,
                    "pension_participants": user.business.pension_participants,
                    "llc_distributes_profit": user.business.llc_distributes_profit,
                }
            )
    return jsonify(payload)


@bp.put("")
@jwt_required()
def update_settings():
    user = current_user()
    data = request.get_json(silent=True) or {}

    if "language" in data and data["language"] in {"ka", "en"}:
        user.language = data["language"]
    if "full_name" in data:
        user.full_name = (data.get("full_name") or "").strip() or None

    obligations = None
    if user.business and "business" in data:
        b = data["business"] or {}
        if "name" in b:
            user.business.name = (b.get("name") or user.business.name).strip()
        if "business_type" in b and b["business_type"]:
            user.business.business_type = b["business_type"]
        if "city" in b and b["city"]:
            user.business.city = b["city"]
        if "lens_expected_receipts_per_day" in b and b["lens_expected_receipts_per_day"] is not None:
            try:
                n = int(b["lens_expected_receipts_per_day"])
                user.business.lens_expected_receipts_per_day = max(1, min(n, 200))
            except (TypeError, ValueError):
                pass

        tax_keys = {
            "legal_form",
            "tax_regime",
            "is_vat_payer",
            "has_employees",
            "pension_participants",
            "llc_distributes_profit",
        }
        if tax_keys & set(b.keys()):
            payload = {
                "legal_form": b.get("legal_form", user.business.legal_form),
                "tax_regime": b.get("tax_regime", user.business.tax_regime),
                "is_vat_payer": b.get("is_vat_payer", user.business.is_vat_payer),
                "has_employees": b.get("has_employees", user.business.has_employees),
                "pension_participants": b.get(
                    "pension_participants", user.business.pension_participants
                ),
                "llc_distributes_profit": b.get(
                    "llc_distributes_profit", user.business.llc_distributes_profit
                ),
            }
            ready, errors, warnings = validate_profile(payload)
            if errors:
                msg = ERROR_MESSAGES.get(errors[0], errors[0])
                return jsonify({"error": msg, "errors": errors, "warnings": warnings}), 400
            _apply_tax_profile(user.business, ready)
            rebuild_tax_reserves(user.business)
            obligations = resolve_obligations(ready)

    db.session.commit()
    payload = {"user": user.to_dict()}
    if user.business:
        payload["business"] = user.business.to_dict()
        if obligations is not None:
            payload["obligations"] = obligations
        elif user.business.tax_profile_complete:
            payload["obligations"] = resolve_obligations(
                {
                    "legal_form": user.business.legal_form,
                    "tax_regime": user.business.tax_regime,
                    "is_vat_payer": user.business.is_vat_payer,
                    "has_employees": user.business.has_employees,
                    "pension_participants": user.business.pension_participants,
                    "llc_distributes_profit": user.business.llc_distributes_profit,
                }
            )
    return jsonify(payload)


@bp.get("/business")
@jwt_required()
@require_business
def get_business(business):
    return jsonify(business.to_dict())
