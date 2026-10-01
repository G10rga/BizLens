"""Lens Mode API — photograph fiscal receipts → sales + forecast data."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from ..config import Config
from ..extensions import db
from ..models import Product, ReceiptCapture, Sale, SaleItem
from ..services.lens_completeness import completeness_report
from ..services.receipt_ocr import (
    combine_sold_at,
    compress_for_ocr,
    empty_manual_parse,
    ocr_status,
    parse_image_safe,
    parse_receipt_text,
    sample_receipt_text,
)
from ..services.sales_agg import upsert_daily_revenue
from .helpers import require_business

bp = Blueprint("lens", __name__, url_prefix="/api/lens")


def _lens_dir(business_id: int) -> Path:
    path = Path(Config.UPLOAD_DIR) / "lens" / str(business_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


@bp.get("/completeness")
@jwt_required()
@require_business
def completeness(business):
    days = request.args.get("days", default=14, type=int)
    return jsonify(completeness_report(business, days=days))


@bp.get("/ocr-status")
@jwt_required()
@require_business
def lens_ocr_status(business):
    """Show which free/paid OCR engines Lens can use."""
    return jsonify(ocr_status())


@bp.get("/history")
@jwt_required()
@require_business
def history(business):
    rows = (
        ReceiptCapture.query.filter_by(business_id=business.id)
        .order_by(ReceiptCapture.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"captures": [r.to_dict() for r in rows]})


@bp.get("/images/<int:capture_id>")
@jwt_required()
@require_business
def image(business, capture_id: int):
    cap = ReceiptCapture.query.filter_by(
        id=capture_id, business_id=business.id
    ).first_or_404()
    if not cap.image_path or not Path(cap.image_path).exists():
        return jsonify({"error": "Image not found"}), 404
    return send_file(cap.image_path)


@bp.post("/expected-receipts")
@jwt_required()
@require_business
def set_expected(business):
    data = request.get_json(silent=True) or {}
    n = int(data.get("expected_per_day") or business.lens_expected_receipts_per_day)
    business.lens_expected_receipts_per_day = max(1, min(n, 200))
    db.session.commit()
    return jsonify(
        {
            "lens_expected_receipts_per_day": business.lens_expected_receipts_per_day,
            "completeness": completeness_report(business, days=14),
        }
    )


@bp.post("/scan-demo")
@jwt_required()
@require_business
def scan_demo(business):
    """Demo Day helper: parse the sample fiscal receipt without a camera."""
    today = date.today()
    # Keep sample layout but stamp today's date so completeness bars move
    raw = sample_receipt_text()
    raw = re.sub(
        r"Date:\s*.*",
        f"Date:     {today.day} {today.strftime('%B')} {today.year}",
        raw,
        count=1,
        flags=re.IGNORECASE,
    )
    parsed = parse_receipt_text(raw)
    parsed["receipt_date"] = today.isoformat()
    cap = ReceiptCapture(
        business_id=business.id,
        raw_text=raw,
        receipt_date=today,
        receipt_time=parsed.get("receipt_time"),
        total=parsed.get("total"),
        payment_method=parsed.get("payment_method") or "unknown",
        tin=parsed.get("tin"),
        items_json=json.dumps(parsed.get("items") or [], ensure_ascii=False),
        parse_confidence=parsed.get("parse_confidence") or 0.9,
        ocr_engine="demo_sample",
        status="draft",
    )
    db.session.add(cap)
    db.session.commit()
    return jsonify(
        {
            "capture": cap.to_dict(),
            "parsed": parsed,
            "demo": True,
        }
    )


@bp.post("/scan")
@jwt_required()
@require_business
def scan(business):
    """Upload a receipt photo (or raw_text) and run OCR + parse into a draft capture."""
    raw_text_override = (request.form.get("raw_text") or "").strip()
    skip_ocr = (request.form.get("skip_ocr") or "").lower() in {"1", "true", "yes"}
    file = request.files.get("file")
    image_bytes = b""
    filename = ""
    saved_path = None

    try:
        if file and file.filename:
            filename = secure_filename(file.filename) or "receipt.jpg"
            image_bytes = file.read()
            if len(image_bytes) > 12 * 1024 * 1024:
                return jsonify({"error": "Image too large (max 12MB). Take a closer photo."}), 400
            if image_bytes:
                from datetime import datetime as _dt

                # Store a compressed copy — keeps disk/memory down
                to_store = compress_for_ocr(image_bytes, max_side=1600)
                saved_path = _lens_dir(business.id) / f"{business.id}_{Path(filename).stem}.jpg"
                if saved_path.exists():
                    saved_path = saved_path.with_name(
                        f"{saved_path.stem}_{_dt.utcnow().strftime('%H%M%S')}.jpg"
                    )
                saved_path.write_bytes(to_store)
                image_bytes = to_store

        if raw_text_override:
            parsed = parse_receipt_text(raw_text_override)
            parsed["raw_text"] = raw_text_override
            parsed["ocr_engine"] = "manual_text"
        elif image_bytes:
            parsed = parse_image_safe(
                image_bytes,
                filename=filename or "receipt.jpg",
                timeout_sec=50,
                skip_ocr=skip_ocr,
            )
        else:
            return jsonify({"error": "file or raw_text is required"}), 400

        try:
            rdate = (
                date.fromisoformat(parsed["receipt_date"])
                if parsed.get("receipt_date")
                else date.today()
            )
        except ValueError:
            rdate = date.today()

        cap = ReceiptCapture(
            business_id=business.id,
            image_path=str(saved_path) if saved_path else None,
            raw_text=parsed.get("raw_text") or "",
            receipt_date=rdate,
            receipt_time=parsed.get("receipt_time"),
            total=parsed.get("total"),
            payment_method=parsed.get("payment_method") or "unknown",
            tin=parsed.get("tin"),
            items_json=json.dumps(parsed.get("items") or [], ensure_ascii=False),
            parse_confidence=float(parsed.get("parse_confidence") or 0),
            ocr_engine=parsed.get("ocr_engine"),
            status="draft",
        )
        db.session.add(cap)
        db.session.commit()
        return jsonify({"capture": cap.to_dict(), "parsed": parsed})
    except Exception as exc:  # noqa: BLE001
        # Last resort — never let Lens take down the site with a 502
        db.session.rollback()
        parsed = empty_manual_parse(
            f"Server recovered after OCR fault ({exc.__class__.__name__}) — enter total manually"
        )
        try:
            rdate = date.today()
            cap = ReceiptCapture(
                business_id=business.id,
                image_path=str(saved_path) if saved_path else None,
                raw_text="",
                receipt_date=rdate,
                receipt_time=None,
                total=None,
                payment_method="cash",
                tin=None,
                items_json="[]",
                parse_confidence=0.0,
                ocr_engine="manual",
                status="draft",
            )
            db.session.add(cap)
            db.session.commit()
            return jsonify({"capture": cap.to_dict(), "parsed": parsed, "recovered": True})
        except Exception as exc2:  # noqa: BLE001
            db.session.rollback()
            return jsonify({"error": f"Scan failed: {exc2}"}), 500


@bp.post("/confirm")
@jwt_required()
@require_business
def confirm(business):
    """
    Confirm a draft capture into a Sale (+ optional line items).
    Body: capture_id, receipt_date, receipt_time, total, payment_method,
          add_items (bool), items (list), tin
    """
    data = request.get_json(silent=True) or {}
    capture_id = data.get("capture_id")
    if not capture_id:
        return jsonify({"error": "capture_id is required"}), 400

    cap = ReceiptCapture.query.filter_by(
        id=int(capture_id), business_id=business.id
    ).first()
    if not cap:
        return jsonify({"error": "Capture not found"}), 404
    if cap.status == "confirmed" and cap.sale_id:
        return jsonify({"error": "Already confirmed", "capture": cap.to_dict()}), 400

    try:
        rdate = date.fromisoformat(data.get("receipt_date") or cap.receipt_date.isoformat())
    except Exception:  # noqa: BLE001
        rdate = cap.receipt_date or date.today()

    rtime = (data.get("receipt_time") or cap.receipt_time or "").strip() or None
    total = data.get("total")
    if total is None:
        total = cap.total
    try:
        total = float(total)
    except (TypeError, ValueError):
        return jsonify({"error": "total is required"}), 400
    if total <= 0:
        return jsonify({"error": "total must be positive"}), 400

    payment = (data.get("payment_method") or cap.payment_method or "cash").strip().lower()
    if payment not in {"cash", "card"}:
        payment = "cash"

    add_items = bool(data.get("add_items"))
    items_in = data.get("items") if add_items else []
    if add_items and not items_in:
        # fall back to OCR items
        try:
            items_in = json.loads(cap.items_json or "[]")
        except Exception:  # noqa: BLE001
            items_in = []

    sold_at = combine_sold_at(rdate, rtime)
    sale = Sale(
        business_id=business.id,
        total=round(total, 2),
        payment_method=payment,
        sold_at=sold_at,
        source="lens",
    )
    db.session.add(sale)
    db.session.flush()

    sale_items = []
    if add_items and items_in:
        running = 0.0
        for raw in items_in:
            name = (raw.get("product_name") or "").strip()
            if not name:
                continue
            qty = int(raw.get("quantity") or 1)
            if qty <= 0:
                continue
            unit = float(raw.get("unit_price") or 0)
            line = raw.get("line_total")
            line_total = float(line) if line is not None else round(unit * qty, 2)
            if unit <= 0 and line_total > 0:
                unit = round(line_total / qty, 2)
            product_id = raw.get("product_id")
            if product_id:
                product = Product.query.filter_by(
                    id=product_id, business_id=business.id
                ).first()
                product_id = product.id if product else None
            else:
                product_id = None
            db.session.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product_id,
                    product_name=name,
                    unit_price=unit,
                    quantity=qty,
                    line_total=line_total,
                )
            )
            sale_items.append(name)
            running += line_total
        # If items don't sum to total, keep receipt total as source of truth
        if sale_items and abs(running - total) > 0.05 and running > 0:
            pass

    if not add_items or not sale_items:
        # Totals-only Lens sale still needs a placeholder line for POS-shaped records
        db.session.add(
            SaleItem(
                sale_id=sale.id,
                product_id=None,
                product_name="Fiscal receipt",
                unit_price=round(total, 2),
                quantity=1,
                line_total=round(total, 2),
            )
        )

    upsert_daily_revenue(business.id, rdate, sale.total, source="lens")
    if payment == "cash":
        business.cash_on_hand = float(business.cash_on_hand) + sale.total

    cap.sale_id = sale.id
    cap.receipt_date = rdate
    cap.receipt_time = rtime
    cap.total = sale.total
    cap.payment_method = payment
    cap.tin = (data.get("tin") or cap.tin or "").strip() or None
    if add_items and items_in:
        cap.items_json = json.dumps(items_in, ensure_ascii=False)
    cap.status = "confirmed"
    db.session.commit()

    return jsonify(
        {
            "capture": cap.to_dict(),
            "sale": sale.to_dict(),
            "completeness": completeness_report(business, days=14),
        }
    ), 201
