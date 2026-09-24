from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from extensions.auth_decorators import roles_required
from models.user import User
from models.role import Role
from models.team import Team
from services.audit_service import log_action

user_bp = Blueprint("users", __name__)


@user_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.name).all()
    return jsonify({"success": True, "message": "OK", "data": [u.to_dict() for u in users]}), 200


@user_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role_name = data.get("role")

    if not name or not email or not password or not role_name:
        return jsonify({"success": False, "message": "name, email, password, and role are required", "errors": {}}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "A user with this email already exists", "errors": {}}), 409

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"success": False, "message": f"Unknown role '{role_name}'", "errors": {}}), 400

    team = None
    if data.get("team_id"):
        team = Team.query.get(data["team_id"])

    user = User(name=name, email=email, role_id=role.id, team_id=team.id if team else None)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    log_action(int(get_jwt_identity()), "USER_CREATED", entity="user", entity_id=user.id)
    return jsonify({"success": True, "message": "User created successfully", "data": user.to_dict()}), 201


@user_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin")
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "role" in data:
        role = Role.query.filter_by(name=data["role"]).first()
        if not role:
            return jsonify({"success": False, "message": f"Unknown role '{data['role']}'", "errors": {}}), 400
        user.role_id = role.id
    if "team_id" in data:
        user.team_id = data["team_id"]

    db.session.commit()
    log_action(int(get_jwt_identity()), "USER_UPDATED", entity="user", entity_id=user.id)
    return jsonify({"success": True, "message": "User updated successfully", "data": user.to_dict()}), 200


@user_bp.route("/roles", methods=["GET"])
@jwt_required()
def list_roles():
    roles = Role.query.all()
    return jsonify({"success": True, "message": "OK", "data": [{"id": r.id, "name": r.name} for r in roles]}), 200


@user_bp.route("/teams", methods=["GET"])
@jwt_required()
def list_teams():
    teams = Team.query.all()
    return jsonify({"success": True, "message": "OK", "data": [{"id": t.id, "name": t.name} for t in teams]}), 200
