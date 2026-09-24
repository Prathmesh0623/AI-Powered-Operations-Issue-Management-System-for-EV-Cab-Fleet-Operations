from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from models.issue import Issue
from services import issue_service
from services.issue_service import IssueServiceError
from services.audit_service import log_action

issue_bp = Blueprint("issues", __name__)


@issue_bp.route("", methods=["POST"])
@jwt_required()
def create_issue():
    data = request.get_json(silent=True) or {}
    reporter_id = int(get_jwt_identity())
    try:
        issue = issue_service.create_issue(data, reporter_id)
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code

    log_action(reporter_id, "ISSUE_CREATED", entity="issue", entity_id=issue.id)
    return jsonify({"success": True, "message": "Issue created successfully", "data": issue.to_dict()}), 201


@issue_bp.route("", methods=["GET"])
@jwt_required()
def list_issues():
    query = Issue.query

    status = request.args.get("status")
    priority = request.args.get("priority")
    category = request.args.get("category")
    vehicle_id = request.args.get("vehicle_id")
    hub_id = request.args.get("hub_id")
    search = request.args.get("search")

    if status:
        query = query.filter(Issue.status == status)
    if priority:
        query = query.filter(Issue.priority == priority)
    if vehicle_id:
        query = query.filter(Issue.vehicle_id == vehicle_id)
    if hub_id:
        query = query.filter(Issue.hub_id == hub_id)
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Issue.title.ilike(like), Issue.description.ilike(like)))

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    paginated = query.order_by(Issue.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "message": "OK",
        "data": {
            "items": [i.to_dict() for i in paginated.items],
            "page": page,
            "per_page": per_page,
            "total": paginated.total,
            "pages": paginated.pages,
        }
    }), 200


@issue_bp.route("/<int:issue_id>", methods=["GET"])
@jwt_required()
def get_issue(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"success": False, "message": "Issue not found", "errors": {}}), 404
    return jsonify({"success": True, "message": "OK", "data": issue.to_dict(include_details=True)}), 200


@issue_bp.route("/<int:issue_id>", methods=["PUT"])
@jwt_required()
def update_issue(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"success": False, "message": "Issue not found", "errors": {}}), 404

    data = request.get_json(silent=True) or {}
    for field in ("title", "description"):
        if field in data:
            setattr(issue, field, data[field])

    db.session.commit()
    return jsonify({"success": True, "message": "Issue updated successfully", "data": issue.to_dict()}), 200


@issue_bp.route("/<int:issue_id>", methods=["DELETE"])
@jwt_required()
def delete_issue(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"success": False, "message": "Issue not found", "errors": {}}), 404
    db.session.delete(issue)
    db.session.commit()
    return jsonify({"success": True, "message": "Issue deleted successfully", "data": {}}), 200


@issue_bp.route("/<int:issue_id>/status", methods=["POST"])
@jwt_required()
def update_status(issue_id):
    data = request.get_json(silent=True) or {}
    changed_by = int(get_jwt_identity())
    old_issue = Issue.query.get(issue_id)
    old_status = old_issue.status if old_issue else None
    try:
        issue = issue_service.change_status(issue_id, data.get("status"), changed_by)
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code
    log_action(changed_by, "ISSUE_STATUS_CHANGE", entity="issue", entity_id=issue.id,
               old_value=old_status, new_value=issue.status)
    return jsonify({"success": True, "message": "Status updated", "data": issue.to_dict()}), 200


@issue_bp.route("/<int:issue_id>/priority", methods=["POST"])
@jwt_required()
def update_priority(issue_id):
    data = request.get_json(silent=True) or {}
    changed_by = int(get_jwt_identity())
    old_issue = Issue.query.get(issue_id)
    old_priority = old_issue.priority if old_issue else None
    try:
        issue = issue_service.change_priority(issue_id, data.get("priority"), changed_by, data.get("reason"))
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code
    log_action(changed_by, "ISSUE_PRIORITY_CHANGE", entity="issue", entity_id=issue.id,
               old_value=old_priority, new_value=issue.priority)
    return jsonify({"success": True, "message": "Priority updated", "data": issue.to_dict()}), 200


@issue_bp.route("/<int:issue_id>/assign", methods=["POST"])
@jwt_required()
def assign(issue_id):
    data = request.get_json(silent=True) or {}
    changed_by = int(get_jwt_identity())
    try:
        issue = issue_service.assign_issue(
            issue_id, changed_by, team_id=data.get("team_id"), user_id=data.get("user_id")
        )
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code
    return jsonify({"success": True, "message": "Issue assigned", "data": issue.to_dict()}), 200


@issue_bp.route("/<int:issue_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(issue_id):
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    try:
        comment = issue_service.add_comment(issue_id, user_id, data.get("comment"))
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code
    return jsonify({"success": True, "message": "Comment added", "data": comment.to_dict()}), 201
