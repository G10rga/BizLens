from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from ..config import Config
from ..extensions import db
from ..models import CsvImport
from ..services.csv_parser import parse_sales_file
from ..services.sales_agg import set_daily_revenue
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
    return jsonify([r.to_dict() for r in rows])


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
    rows, warnings = parse_sales_file(raw, filename=file.filename)
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

    filename = secure_filename(file.filename) or "upload.xlsx"
    raw = file.read()
    save_path = Path(Config.UPLOAD_DIR) / f"{business.id}_{filename}"
    save_path.write_bytes(raw)

    try:
        rows, warnings = parse_sales_file(raw, filename=file.filename)
        for row in rows:
            set_daily_revenue(
                business.id,
                date.fromisoformat(row["date"]),
                row["revenue"],
                source="csv",
            )
        record = CsvImport(
            business_id=business.id,
            filename=filename,
            rows_imported=len(rows),
            status="completed",
            message="; ".join(warnings) if warnings else "OK",
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(
            {
                "import": record.to_dict(),
                "rows_imported": len(rows),
                "warnings": warnings,
            }
        )
    except Exception as exc:  # noqa: BLE001
        record = CsvImport(
            business_id=business.id,
            filename=filename,
            rows_imported=0,
            status="failed",
            message=str(exc),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"error": str(exc), "import": record.to_dict()}), 400
