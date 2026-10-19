from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from ..config import Config
from ..extensions import db
from ..models import Alert, CsvImport, DailySale, ReceiptCapture, Sale, SaleItem
from ..services.csv_parser import parse_sales_file
from ..services.sales_agg import set_daily_revenue
from ..services.tax_accrual import rebuild_tax_reserves
from .helpers import require_business

bp = Blueprint("csv_import", __name__, url_prefix="/api/csv")


@bp.get("/history")
@jwt_required()
@require_business
def history(business):
    rows = (
        CsvImport.query.filter_by(business_id=business.id)
        .order_by(CsvImport.created_at.desc())
        .limit(50)
        .all()
    )
    daily_count = DailySale.query.filter_by(business_id=business.id).count()
    return jsonify(
        {
            "imports": [r.to_dict() for r in rows],
            "daily_sales_days": daily_count,
        }
    )


@bp.delete("/data")
@jwt_required()
@require_business
def clear_data(business):
    """Delete imported / forecast sales data so a fresh file can be uploaded."""
    data = request.get_json(silent=True) or {}
    include_pos = data.get("include_pos", True)

    try:
        daily_deleted = DailySale.query.filter_by(business_id=business.id).delete(
            synchronize_session=False
        )
        imports_deleted = CsvImport.query.filter_by(business_id=business.id).delete(
            synchronize_session=False
        )
        alerts_deleted = Alert.query.filter_by(business_id=business.id).delete(
            synchronize_session=False
        )

        pos_deleted = 0
        if include_pos:
            sale_id_list = [
                row[0]
                for row in db.session.query(Sale.id)
                .filter_by(business_id=business.id)
                .all()
            ]
            # Bulk Sale.delete() skips ORM cascades — remove FK children first.
            if sale_id_list:
                SaleItem.query.filter(SaleItem.sale_id.in_(sale_id_list)).delete(
                    synchronize_session=False
                )
                ReceiptCapture.query.filter(
                    ReceiptCapture.sale_id.in_(sale_id_list)
                ).delete(synchronize_session=False)
            # Also drop any leftover Lens drafts for this business
            ReceiptCapture.query.filter_by(business_id=business.id).delete(
                synchronize_session=False
            )
            cash_total = (
                db.session.query(func.coalesce(func.sum(Sale.total), 0.0))
                .filter_by(business_id=business.id, payment_method="cash")
                .scalar()
            )
            business.cash_on_hand = max(
                0.0, float(business.cash_on_hand) - float(cash_total or 0)
            )
            pos_deleted = Sale.query.filter_by(business_id=business.id).delete(
                synchronize_session=False
            )

        upload_dir = Path(Config.UPLOAD_DIR)
        files_deleted = 0
        if upload_dir.exists():
            for path in upload_dir.glob(f"{business.id}_*"):
                try:
                    path.unlink()
                    files_deleted += 1
                except OSError:
                    pass

        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({"error": str(exc) or "Could not clear sales data"}), 500

    return jsonify(
        {
            "ok": True,
            "daily_sales_deleted": daily_deleted,
            "imports_deleted": imports_deleted,
            "alerts_deleted": alerts_deleted,
            "pos_sales_deleted": pos_deleted,
            "files_deleted": files_deleted,
        }
    )


@bp.post("/preview")
@jwt_required()
@require_business
def preview(business):
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    raw = file.read()
    if not raw:
        return jsonify({"error": "File is empty"}), 400
    try:
        rows, warnings = parse_sales_file(raw, filename=file.filename)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc) or "Could not parse file"}), 400
    if not rows:
        return jsonify({"error": "No valid Date/Total rows found"}), 400
    return jsonify(
        {
            "preview": rows[:30],
            "total_rows": len(rows),
            "date_from": rows[0]["date"],
            "date_to": rows[-1]["date"],
            "warnings": warnings,
        }
    )


@bp.post("/import")
@jwt_required()
@require_business
def import_csv(business):
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    replace = (request.form.get("replace") or "false").lower() in {"1", "true", "yes"}
    filename = secure_filename(file.filename) or "upload.xlsx"
    raw = file.read()
    if not raw:
        return jsonify({"error": "File is empty"}), 400

    upload_dir = Path(Config.UPLOAD_DIR)
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        save_path = upload_dir / f"{business.id}_{filename}"
        save_path.write_bytes(raw)
    except OSError as exc:
        # Don't block import if the upload archive can't be written (e.g. bad perms)
        save_path = None
        warnings_prefix = f"upload save skipped ({exc}); "
    else:
        warnings_prefix = ""

    try:
        if replace:
            DailySale.query.filter_by(business_id=business.id).delete()
            Alert.query.filter_by(business_id=business.id).delete()

        rows, warnings = parse_sales_file(raw, filename=file.filename)
        for row in rows:
            set_daily_revenue(
                business.id,
                date.fromisoformat(row["date"]),
                row["revenue"],
                source="csv",
            )
        rebuild_tax_reserves(business)
        msg_bits = []
        if warnings_prefix:
            msg_bits.append(warnings_prefix.strip("; "))
        if replace:
            msg_bits.append("replaced")
        if warnings:
            msg_bits.extend(warnings)
        if not msg_bits:
            msg_bits.append("OK")
        record = CsvImport(
            business_id=business.id,
            filename=filename,
            rows_imported=len(rows),
            status="completed",
            message="; ".join(msg_bits),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(
            {
                "import": record.to_dict(),
                "rows_imported": len(rows),
                "replaced": replace,
                "warnings": warnings,
                "file_saved": save_path is not None,
                "tax_reserve": float(business.tax_reserve or 0),
                "vat_reserve": float(business.vat_reserve or 0),
            }
        )
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        try:
            record = CsvImport(
                business_id=business.id,
                filename=filename,
                rows_imported=0,
                status="failed",
                message=str(exc)[:500],
            )
            db.session.add(record)
            db.session.commit()
            return jsonify({"error": str(exc), "import": record.to_dict()}), 400
        except Exception:  # noqa: BLE001
            db.session.rollback()
            return jsonify({"error": str(exc)}), 400
