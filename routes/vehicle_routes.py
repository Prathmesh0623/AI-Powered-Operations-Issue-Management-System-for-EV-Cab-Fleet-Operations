from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.vehicle import Vehicle, VEHICLE_STATUSES
from services.audit_service import log_action

vehicle_bp = Blueprint("vehicles", __name__)


@vehicle_bp.route("", methods=["GET"])
@jwt_required()
def list_vehicles():
    query = Vehicle.query
    status = request.args.get("status")
    hub_id = request.args.get("hub_id")
    if status:
        query = query.filter(Vehicle.status == status)
    if hub_id:
        query = query.filter(Vehicle.hub_id == hub_id)
    vehicles = query.order_by(Vehicle.registration_number).all()
    return jsonify({"success": True, "message": "OK", "data": [v.to_dict() for v in vehicles]}), 200


@vehicle_bp.route("/<int:vehicle_id>", methods=["GET"])
@jwt_required()
def get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({"success": False, "message": "Vehicle not found", "errors": {}}), 404

    data = vehicle.to_dict()
    data["recent_issues"] = [i.to_dict() for i in sorted(vehicle.issues, key=lambda i: i.created_at, reverse=True)[:10]]
    data["maintenance_history"] = [m.to_dict() for m in vehicle.maintenance_records]
    return jsonify({"success": True, "message": "OK", "data": data}), 200


@vehicle_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_vehicle():
    data = request.get_json(silent=True) or {}
    reg = (data.get("registration_number") or "").strip()
    if not reg:
        return jsonify({"success": False, "message": "registration_number is required", "errors": {}}), 400
    if Vehicle.query.filter_by(registration_number=reg).first():
        return jsonify({"success": False, "message": "A vehicle with this registration number already exists", "errors": {}}), 409

    status = data.get("status", "Available")
    if status not in VEHICLE_STATUSES:
        return jsonify({"success": False, "message": f"status must be one of {VEHICLE_STATUSES}", "errors": {}}), 400

    vehicle = Vehicle(
        registration_number=reg,
        model=data.get("model"),
        battery_percentage=data.get("battery_percentage", 100.0),
        status=status,
        hub_id=data.get("hub_id"),
    )
    db.session.add(vehicle)
    db.session.commit()

    log_action(int(get_jwt_identity()), "VEHICLE_CREATED", entity="vehicle", entity_id=vehicle.id)
    return jsonify({"success": True, "message": "Vehicle created successfully", "data": vehicle.to_dict()}), 201


@vehicle_bp.route("/<int:vehicle_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin", "ops_manager")
def update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({"success": False, "message": "Vehicle not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    old_status = vehicle.status

    if "status" in data:
        if data["status"] not in VEHICLE_STATUSES:
            return jsonify({"success": False, "message": f"status must be one of {VEHICLE_STATUSES}", "errors": {}}), 400
        vehicle.status = data["status"]
    for field in ("model", "battery_percentage", "hub_id"):
        if field in data:
            setattr(vehicle, field, data[field])

    db.session.commit()

    if "status" in data and data["status"] != old_status:
        log_action(int(get_jwt_identity()), "VEHICLE_STATUS_CHANGE", entity="vehicle", entity_id=vehicle.id,
                   old_value=old_status, new_value=vehicle.status)

    return jsonify({"success": True, "message": "Vehicle updated successfully", "data": vehicle.to_dict()}), 200
