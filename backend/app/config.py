import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")


def _database_uri() -> str:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        return f"sqlite:///{(INSTANCE_DIR / 'bizlens.db').as_posix()}"
    # Normalize relative sqlite paths to backend/instance
    if raw.startswith("sqlite:///"):
        rest = raw[len("sqlite:///") :]
        if rest.startswith("instance/") or rest == "instance/bizlens.db":
            return f"sqlite:///{(INSTANCE_DIR / Path(rest).name).as_posix()}"
        path = Path(rest)
        if not path.is_absolute():
            return f"sqlite:///{(BASE_DIR / rest).resolve().as_posix()}"
    return raw


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "bizlens-dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "bizlens-jwt-dev-secret")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    DEMO_SEED = os.getenv("DEMO_SEED", "true").lower() in {"1", "true", "yes"}
    FRONTEND_DIST = PROJECT_ROOT / "web" / "dist"
    STITCH_DIR = PROJECT_ROOT / "frontend"
    UPLOAD_DIR = INSTANCE_DIR / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    CASH_GREEN_THRESHOLD = 1500.0
    CASH_YELLOW_THRESHOLD = 500.0
    FORECAST_HORIZON_DAYS = 90
