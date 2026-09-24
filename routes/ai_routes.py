from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions.database import db
from models.issue import Issue
from models.ai_prediction import AIPrediction
from ml.inference.category_predictor import predict_category, is_ready as category_ready
from ml.inference.priority_predictor import predict_priority, is_ready as priority_ready
from ml.inference.similarity_engine import find_similar_issues
from services import impact_service
from services.issue_service import IssueServiceError
from services.audit_service import log_action
from models.issue import ISSUE_PRIORITIES

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/classify", methods=["POST"])
@jwt_required()
def classify():
    data = request.get_json(silent=True) or {}
    title, description = data.get("title", ""), data.get("description", "")
    if not description:
        return jsonify({"success": False, "message": "description is required", "errors": {}}), 400

    if not category_ready():
        return jsonify({
            "success": False,
            "message": "Category model has not been trained yet. Run ml/training/train_category.py first.",
            "errors": {}
        }), 503

    category, confidence = predict_category(title, description)
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"predicted_category": category, "confidence": confidence}
    }), 200


@ai_bp.route("/priority", methods=["POST"])
@jwt_required()
def priority():
    data = request.get_json(silent=True) or {}
    title, description = data.get("title", ""), data.get("description", "")
    category = data.get("category", "Other")
    if not description:
        return jsonify({"success": False, "message": "description is required", "errors": {}}), 400

    if not priority_ready():
        return jsonify({
            "success": False,
            "message": "Priority model has not been trained yet. Run ml/training/train_priority.py first.",
            "errors": {}
        }), 503

    predicted_priority, confidence = predict_priority(title, description, category)
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"predicted_priority": predicted_priority, "confidence": confidence}
    }), 200


@ai_bp.route("/similarity", methods=["POST"])
@jwt_required()
def similarity():
    data = request.get_json(silent=True) or {}
    title, description = data.get("title", ""), data.get("description", "")
    exclude_id = data.get("exclude_issue_id")
    if not description:
        return jsonify({"success": False, "message": "description is required", "errors": {}}), 400

    query = Issue.query.filter(Issue.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"]))
    if exclude_id:
        query = query.filter(Issue.id != exclude_id)
    candidates = [(c.id, c.title, c.description) for c in query.limit(200).all()]

    matches = find_similar_issues(title, description, candidates)
    results = []
    for issue_id, score in matches:
        related = Issue.query.get(issue_id)
        results.append({
            "issue_id": issue_id,
            "title": related.title if related else None,
            "similarity_score": round(score * 100, 1),
        })

    return jsonify({"success": True, "message": "OK", "data": results}), 200


@ai_bp.route("/issues/<int:issue_id>/impact-analysis", methods=["GET"])
@jwt_required()
def impact_analysis(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"success": False, "message": "Issue not found", "errors": {}}), 404

    level, explanation = impact_service.assess_impact(issue)
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"operational_impact": level, "explanation": explanation}
    }), 200


@ai_bp.route("/issues/<int:issue_id>/ai-analysis", methods=["GET"])
@jwt_required()
def issue_ai_analysis(issue_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"success": False, "message": "Issue not found", "errors": {}}), 404

    latest = (AIPrediction.query.filter_by(issue_id=issue_id)
              .order_by(AIPrediction.created_at.desc()).first())

    if not latest:
        return jsonify({
            "success": True,
            "message": "No AI analysis stored for this issue yet",
            "data": {
                "ai_predicted_category": issue.ai_predicted_category,
                "ai_predicted_priority": issue.ai_predicted_priority,
            }
        }), 200

    return jsonify({"success": True, "message": "OK", "data": latest.to_dict()}), 200


@ai_bp.route("/issues/<int:issue_id>/priority-override", methods=["POST"])
@jwt_required()
def override_priority(issue_id):
    """Lets a manager confirm or change the AI-suggested priority, with a reason."""
    data = request.get_json(silent=True) or {}
    new_priority = data.get("priority")
    reason = data.get("reason")

    if new_priority not in ISSUE_PRIORITIES:
        return jsonify({"success": False, "message": f"priority must be one of {ISSUE_PRIORITIES}", "errors": {}}), 400

    from services import issue_service
    changed_by = int(get_jwt_identity())
    try:
        issue = issue_service.change_priority(issue_id, new_priority, changed_by, reason)
    except IssueServiceError as e:
        return jsonify({"success": False, "message": e.message, "errors": {}}), e.status_code

    log_action(changed_by, "PRIORITY_OVERRIDE", entity="issue", entity_id=issue.id,
               old_value=issue.ai_predicted_priority, new_value=new_priority)
    return jsonify({"success": True, "message": "Priority override recorded", "data": issue.to_dict()}), 200
