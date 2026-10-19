from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt
from . import models  # noqa: F401
from .routes import (
    alerts,
    auth,
    csv_import,
    expenses,
    forecast,
    lens,
    onboarding,
    products,
    sales,
    settings,
    tax,
)
from .seed import seed_demo_if_needed


def create_app(config_object=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object)

    # HTTPS / correct host behind Render's reverse proxy
    if app.config.get("IS_PRODUCTION"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    app.register_blueprint(auth.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(sales.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(forecast.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(csv_import.bp)
    app.register_blueprint(lens.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(tax.bp)

    dist = Path(app.config["FRONTEND_DIST"])
    stitch = Path(app.config["STITCH_DIR"])
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "BizLens"})

    @app.get("/")
    def index():
        return send_from_directory(dist, "index.html")

    @app.get("/assets/<path:filename>")
    def spa_assets(filename):
        return send_from_directory(dist / "assets", filename)

    @app.get("/stitch/<path:filename>")
    def stitch_assets(filename):
        if not stitch.exists():
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(stitch, filename)

    @app.errorhandler(404)
    def spa_fallback(e):
        # API 404s stay JSON; UI routes fall back to SPA
        from flask import request

        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        # Serve other Vite build files (favicon.svg, etc.)
        rel = request.path.lstrip("/")
        if rel and ".." not in rel:
            candidate = dist / rel
            if candidate.is_file():
                return send_from_directory(dist, rel)
        if dist.joinpath("index.html").exists():
            return send_from_directory(dist, "index.html")
        return jsonify({"error": "Frontend not built. Run: cd web && npm run build"}), 503

    @app.errorhandler(500)
    def api_internal_error(e):
        from flask import request

        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return e

    @app.errorhandler(Exception)
    def api_unhandled_exception(e):
        from flask import request
        from werkzeug.exceptions import HTTPException

        if isinstance(e, HTTPException):
            return e
        if request.path.startswith("/api/"):
            app.logger.exception("Unhandled API error on %s", request.path)
            return jsonify({"error": str(e) or "Internal server error"}), 500
        raise e

    with app.app_context():
        db.create_all()
        _ensure_schema_compat()
        if app.config.get("DEMO_SEED"):
            seed_demo_if_needed(app)

    return app


def _ensure_schema_compat() -> None:
    """Lightweight patches for additive columns (no Alembic yet)."""
    try:
        from sqlalchemy import inspect, text

        eng = db.engine
        dialect = eng.dialect.name
        insp = inspect(eng)
        tables = set(insp.get_table_names())

        if "businesses" in tables:
            cols = {c["name"] for c in insp.get_columns("businesses")}
            business_patches = []
            if "lens_expected_receipts_per_day" not in cols:
                business_patches.append(
                    "ADD COLUMN lens_expected_receipts_per_day INTEGER NOT NULL DEFAULT 10"
                )
            tax_cols = [
                ("legal_form", "VARCHAR(16)"),
                ("tax_regime", "VARCHAR(32)"),
                ("is_vat_payer", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("has_employees", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("pension_participants", "BOOLEAN NOT NULL DEFAULT TRUE"),
                ("llc_distributes_profit", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("tax_profile_complete", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ("tax_reserve", "FLOAT NOT NULL DEFAULT 0"),
                ("vat_reserve", "FLOAT NOT NULL DEFAULT 0"),
            ]
            for col_name, col_type in tax_cols:
                if col_name not in cols:
                    business_patches.append(f"ADD COLUMN {col_name} {col_type}")
            if business_patches:
                with eng.begin() as conn:
                    for patch in business_patches:
                        conn.execute(text(f"ALTER TABLE businesses {patch}"))

        if "products" in tables:
            cols = {c["name"] for c in insp.get_columns("products")}
            with eng.begin() as conn:
                if "barcode" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN barcode VARCHAR(64)"))
                if "image_path" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN image_path VARCHAR(512)"))
    except Exception:  # noqa: BLE001
        pass
