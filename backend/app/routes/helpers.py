from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import Business, User


def current_user() -> User | None:
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id))


def current_business() -> Business | None:
    user = current_user()
    if not user:
        return None
    return user.business


def require_business(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        business = current_business()
        if not business:
            return jsonify({"error": "Complete onboarding first"}), 400
        return fn(business, *args, **kwargs)

    return wrapper
