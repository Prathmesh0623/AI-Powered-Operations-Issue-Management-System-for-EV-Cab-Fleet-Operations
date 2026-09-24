from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.charging_station import ChargingStation, STATION_STATUSES
from models.charging_session import ChargingSession
from models.vehicle import Vehicle
from services.audit_service import log_action

charging_bp = Blueprint("charging", __name__)


@charging_bp.route("/stations", methods=["GET"])
@jwt_required()
def list_stations():
    query = ChargingStation.query
    hub_id = request.args.get("hub_id")
    if hub_id:
        query = query.filter(ChargingStation.hub_id == hub_id)
    stations = query.all()
    return jsonify({"success": True, "message": "OK", "data": [s.to_dict() for s in stations]}), 200


@charging_bp.route("/stations", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_station():
    data = request.get_json(silent=True) or {}
    hub_id = data.get("hub_id")
    if not hub_id:
        return jsonify({"success": False, "message": "hub_id is required", "errors": {}}), 400

    status = data.get("status", "Available")
    if status not in STATION_STATUSES:
        return jsonify({"success": False, "message": f"status must be one of {STATION_STATUSES}", "errors": {}}), 400

    station = ChargingStation(hub_id=hub_id, status=status, capacity=data.get("capacity", 1))
    db.session.add(station)
    db.session.commit()
    log_action(int(get_jwt_identity()), "STATION_CREATED", entity="charging_station", entity_id=station.id)
    return jsonify({"success": True, "message": "Charging station created", "data": station.to_dict()}), 201


@charging_bp.route("/stations/<int:station_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin", "ops_manager", "maintenance")
def update_station(station_id):
    station = ChargingStation.query.get(station_id)
    if not station:
        return jsonify({"success": False, "message": "Charging station not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    if "status" in data:
        if data["status"] not in STATION_STATUSES:
            return jsonify({"success": False, "message": f"status must be one of {STATION_STATUSES}", "errors": {}}), 400
        station.status = data["status"]
    if "capacity" in data:
        station.capacity = data["capacity"]
    db.session.commit()
    return jsonify({"success": True, "message": "Charging station updated", "data": station.to_dict()}), 200


@charging_bp.route("/sessions", methods=["POST"])
@jwt_required()
def start_session():
    data = request.get_json(silent=True) or {}
    station_id = data.get("station_id")
    vehicle_id = data.get("vehicle_id")
    if not station_id or not vehicle_id:
        return jsonify({"success": False, "message": "station_id and vehicle_id are required", "errors": {}}), 400

    station = ChargingStation.query.get(station_id)
    vehicle = Vehicle.query.get(vehicle_id)
    if not station or not vehicle:
        return jsonify({"success": False, "message": "Invalid station or vehicle", "errors": {}}), 404
    if station.status != "Available":
        return jsonify({"success": False, "message": "Charging station is not available", "errors": {}}), 409

    session = ChargingSession(station_id=station_id, vehicle_id=vehicle_id, start_time=datetime.utcnow())
    station.status = "Occupied"
    vehicle.status = "Charging"
    db.session.add(session)
    db.session.commit()
    return jsonify({"success": True, "message": "Charging session started", "data": session.to_dict()}), 201


@charging_bp.route("/sessions/<int:session_id>/end", methods=["POST"])
@jwt_required()
def end_session(session_id):
    session = ChargingSession.query.get(session_id)
    if not session:
        return jsonify({"success": False, "message": "Charging session not found", "errors": {}}), 404
    if session.end_time:
        return jsonify({"success": False, "message": "Session already ended", "errors": {}}), 409

    session.end_time = datetime.utcnow()
    session.station.status = "Available"
    session.vehicle.status = "Available"
    db.session.commit()
    return jsonify({"success": True, "message": "Charging session ended", "data": session.to_dict()}), 200
