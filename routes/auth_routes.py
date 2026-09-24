from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from extensions.database import db
from models.user import User
from services.audit_service import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required", "errors": {}}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid email or password", "errors": {}}), 401

    if not user.is_active:
        return jsonify({"success": False, "message": "This account has been disabled", "errors": {}}), 403

    additional_claims = {"role": user.role.name if user.role else None, "name": user.name}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

    log_action(user_id=user.id, action="LOGIN", entity="user", entity_id=user.id)

    return jsonify({
        "success": True,
        "message": "Login successful",
        "data": {"access_token": access_token, "user": user.to_dict()}
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # JWTs here are stateless; the client is responsible for discarding the token.
    # A token blocklist can be added later if immediate server-side revocation is required.
    user_id = get_jwt_identity()
    log_action(user_id=user_id, action="LOGOUT", entity="user", entity_id=user_id)
    return jsonify({"success": True, "message": "Logged out successfully", "data": {}}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found", "errors": {}}), 404
    return jsonify({"success": True, "message": "OK", "data": user.to_dict()}), 200
