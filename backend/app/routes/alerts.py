from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Alert
from .forecast import regenerate_alerts
from .helpers import require_business

bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


@bp.get("")
@jwt_required()
@require_business
def list_alerts(business):
    alerts = (
        Alert.query.filter_by(business_id=business.id)
        .order_by(Alert.acknowledged.asc(), Alert.created_at.desc())
        .all()
    )
    if not alerts:
        alerts = regenerate_alerts(business)
    return jsonify([a.to_dict() for a in alerts])


@bp.post("/<int:alert_id>/acknowledge")
@jwt_required()
@require_business
def acknowledge(business, alert_id):
    alert = Alert.query.filter_by(id=alert_id, business_id=business.id).first_or_404()
    alert.acknowledged = True
    db.session.commit()
    return jsonify(alert.to_dict())


@bp.post("/generate")
@jwt_required()
@require_business
def generate(business):
    alerts = regenerate_alerts(business)
    return jsonify([a.to_dict() for a in alerts])
