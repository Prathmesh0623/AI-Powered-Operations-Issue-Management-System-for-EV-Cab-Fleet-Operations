from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.hub import Hub
from services.audit_service import log_action

hub_bp = Blueprint("hubs", __name__)


@hub_bp.route("", methods=["GET"])
@jwt_required()
def list_hubs():
    hubs = Hub.query.order_by(Hub.name).all()
    return jsonify({"success": True, "message": "OK", "data": [h.to_dict() for h in hubs]}), 200


@hub_bp.route("/<int:hub_id>", methods=["GET"])
@jwt_required()
def get_hub(hub_id):
    hub = Hub.query.get(hub_id)
    if not hub:
        return jsonify({"success": False, "message": "Hub not found", "errors": {}}), 404

    open_issues = [i for i in hub.issues if i.status not in ("RESOLVED", "CLOSED", "REJECTED")]
    data = hub.to_dict()
    data.update({
        "available_vehicles": sum(1 for v in hub.vehicles if v.status == "Available"),
        "charging_stations": [c.to_dict() for c in hub.charging_stations],
        "open_issues": len(open_issues),
        "critical_issues": sum(1 for i in open_issues if i.priority == "Critical"),
        "drivers": [d.to_dict() for d in hub.drivers],
    })
    return jsonify({"success": True, "message": "OK", "data": data}), 200


@hub_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_hub():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "name is required", "errors": {}}), 400

    hub = Hub(name=name, location=data.get("location"), capacity=data.get("capacity", 0))
    db.session.add(hub)
    db.session.commit()
    log_action(int(get_jwt_identity()), "HUB_CREATED", entity="hub", entity_id=hub.id)
    return jsonify({"success": True, "message": "Hub created successfully", "data": hub.to_dict()}), 201


@hub_bp.route("/<int:hub_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin")
def update_hub(hub_id):
    hub = Hub.query.get(hub_id)
    if not hub:
        return jsonify({"success": False, "message": "Hub not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    for field in ("name", "location", "capacity"):
        if field in data:
            setattr(hub, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "message": "Hub updated successfully", "data": hub.to_dict()}), 200
