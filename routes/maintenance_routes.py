from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.maintenance import Maintenance, MAINTENANCE_STATUSES
from services.audit_service import log_action

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.route("", methods=["GET"])
@jwt_required()
def list_maintenance():
    query = Maintenance.query
    status = request.args.get("status")
    vehicle_id = request.args.get("vehicle_id")
    if status:
        query = query.filter(Maintenance.status == status)
    if vehicle_id:
        query = query.filter(Maintenance.vehicle_id == vehicle_id)
    records = query.order_by(Maintenance.created_at.desc()).all()
    return jsonify({"success": True, "message": "OK", "data": [m.to_dict() for m in records]}), 200


@maintenance_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin", "ops_manager", "maintenance")
def create_maintenance():
    data = request.get_json(silent=True) or {}
    vehicle_id = data.get("vehicle_id")
    if not vehicle_id:
        return jsonify({"success": False, "message": "vehicle_id is required", "errors": {}}), 400

    record = Maintenance(
        vehicle_id=vehicle_id,
        issue_id=data.get("issue_id"),
        maintenance_type=data.get("maintenance_type", "General"),
        status=data.get("status", "Scheduled"),
        technician_team=data.get("technician_team"),
    )
    db.session.add(record)
    db.session.commit()
    log_action(int(get_jwt_identity()), "MAINTENANCE_CREATED", entity="maintenance", entity_id=record.id)
    return jsonify({"success": True, "message": "Maintenance record created", "data": record.to_dict()}), 201


@maintenance_bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin", "ops_manager", "maintenance")
def update_maintenance(record_id):
    record = Maintenance.query.get(record_id)
    if not record:
        return jsonify({"success": False, "message": "Maintenance record not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    if "status" in data:
        if data["status"] not in MAINTENANCE_STATUSES:
            return jsonify({"success": False, "message": f"status must be one of {MAINTENANCE_STATUSES}", "errors": {}}), 400
        record.status = data["status"]
    for field in ("maintenance_type", "technician_team", "resolution_notes"):
        if field in data:
            setattr(record, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "message": "Maintenance record updated", "data": record.to_dict()}), 200
