from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from models.notification import Notification

notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"items": [n.to_dict() for n in notifs], "unread_count": unread_count}
    }), 200


@notification_bp.route("/<int:notification_id>/read", methods=["POST"])
@jwt_required()
def mark_read(notification_id):
    user_id = int(get_jwt_identity())
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notif:
        return jsonify({"success": False, "message": "Notification not found", "errors": {}}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({"success": True, "message": "Marked as read", "data": notif.to_dict()}), 200


@notification_bp.route("/read-all", methods=["POST"])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True, "message": "All notifications marked as read", "data": {}}), 200
