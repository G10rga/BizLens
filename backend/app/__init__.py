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
)
from .seed import seed_demo_if_needed


def create_app(config_object=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object)

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

    dist = app.config["FRONTEND_DIST"]
    stitch = app.config["STITCH_DIR"]
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
        return send_from_directory(stitch, filename)

    @app.errorhandler(404)
    def spa_fallback(e):
        # API 404s stay JSON; UI routes fall back to SPA
        from flask import request

        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        if dist.joinpath("index.html").exists():
            return send_from_directory(dist, "index.html")
        return jsonify({"error": "Frontend not built. Run: cd web && npm run build"}), 503

    with app.app_context():
        db.create_all()
        _ensure_schema_compat()
        if app.config.get("DEMO_SEED"):
            seed_demo_if_needed(app)

    return app


def _ensure_schema_compat() -> None:
    """Lightweight SQLite patches for additive columns (no Alembic yet)."""
    try:
        from sqlalchemy import inspect, text

        eng = db.engine
        if eng.dialect.name != "sqlite":
            return
        insp = inspect(eng)
        if "businesses" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("businesses")}
        if "lens_expected_receipts_per_day" not in cols:
            with eng.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE businesses "
                        "ADD COLUMN lens_expected_receipts_per_day INTEGER NOT NULL DEFAULT 10"
                    )
                )
    except Exception:  # noqa: BLE001
        pass
