from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.driver import Driver, DRIVER_STATUSES
from services.audit_service import log_action

driver_bp = Blueprint("drivers", __name__)


@driver_bp.route("", methods=["GET"])
@jwt_required()
def list_drivers():
    query = Driver.query
    status = request.args.get("status")
    hub_id = request.args.get("hub_id")
    if status:
        query = query.filter(Driver.status == status)
    if hub_id:
        query = query.filter(Driver.hub_id == hub_id)
    drivers = query.order_by(Driver.name).all()
    return jsonify({"success": True, "message": "OK", "data": [d.to_dict() for d in drivers]}), 200


@driver_bp.route("/<int:driver_id>", methods=["GET"])
@jwt_required()
def get_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({"success": False, "message": "Driver not found", "errors": {}}), 404
    data = driver.to_dict()
    data["recent_issues"] = [i.to_dict() for i in sorted(driver.issues, key=lambda i: i.created_at, reverse=True)[:10]]
    return jsonify({"success": True, "message": "OK", "data": data}), 200


@driver_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_driver():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "name is required", "errors": {}}), 400

    status = data.get("status", "Available")
    if status not in DRIVER_STATUSES:
        return jsonify({"success": False, "message": f"status must be one of {DRIVER_STATUSES}", "errors": {}}), 400

    driver = Driver(name=name, contact=data.get("contact"), status=status,
                     hub_id=data.get("hub_id"), vehicle_id=data.get("vehicle_id"))
    db.session.add(driver)
    db.session.commit()
    log_action(int(get_jwt_identity()), "DRIVER_CREATED", entity="driver", entity_id=driver.id)
    return jsonify({"success": True, "message": "Driver created successfully", "data": driver.to_dict()}), 201


@driver_bp.route("/<int:driver_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin", "ops_manager")
def update_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({"success": False, "message": "Driver not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    if "status" in data:
        if data["status"] not in DRIVER_STATUSES:
            return jsonify({"success": False, "message": f"status must be one of {DRIVER_STATUSES}", "errors": {}}), 400
        driver.status = data["status"]
    for field in ("name", "contact", "hub_id", "vehicle_id"):
        if field in data:
            setattr(driver, field, data[field])

    db.session.commit()
    return jsonify({"success": True, "message": "Driver updated successfully", "data": driver.to_dict()}), 200
