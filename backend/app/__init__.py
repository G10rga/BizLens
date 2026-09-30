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
    onboarding,
    products,
    sales,
    settings,
)
from .seed import seed_demo_if_needed


def create_app(config_object=Config):
    app = Flask(
        __name__,
        static_folder=str(config_object.FRONTEND_DIR),
        static_url_path="/ui",
    )
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
    app.register_blueprint(settings.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "BizLens"})

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    with app.app_context():
        db.create_all()
        if app.config.get("DEMO_SEED"):
            seed_demo_if_needed(app)

    return app
