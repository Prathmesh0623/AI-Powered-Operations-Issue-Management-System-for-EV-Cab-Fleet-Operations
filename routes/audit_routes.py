from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions.auth_decorators import roles_required
from models.audit_log import AuditLog

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def list_audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    paginated = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {
            "items": [a.to_dict() for a in paginated.items],
            "page": page,
            "total": paginated.total,
            "pages": paginated.pages,
        }
    }), 200
