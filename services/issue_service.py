from extensions.database import db
from models.issue import Issue, VALID_TRANSITIONS, ISSUE_PRIORITIES
from models.issue_history import IssueHistory
from models.issue_comment import IssueComment
from models.issue_category import IssueCategory
from models.ai_prediction import AIPrediction
from models.similar_issue import SimilarIssue
from models.vehicle import Vehicle
from ml.inference.category_predictor import predict_category, is_ready as category_ready
from ml.inference.priority_predictor import predict_priority, is_ready as priority_ready
from ml.inference.similarity_engine import find_similar_issues
from services import impact_service
from services import notification_service


class IssueServiceError(Exception):
    """Raised for business-rule violations (invalid transition, bad field, etc.)."""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_issue(data, reporter_id):
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    if not title or not description:
        raise IssueServiceError("Title and description are required")

    category = None
    category_name = data.get("category")
    if category_name:
        category = IssueCategory.query.filter_by(name=category_name).first()
        if not category:
            category = IssueCategory(name=category_name)
            db.session.add(category)
            db.session.flush()

    priority = data.get("priority", "Medium")
    if priority not in ISSUE_PRIORITIES:
        priority = "Medium"

    vehicle_id = data.get("vehicle_id")
    hub_id = data.get("hub_id")

    # If a vehicle is linked but no hub was explicitly chosen, inherit the
    # vehicle's hub — otherwise this issue would silently not count toward
    # that hub's issue totals even though it clearly belongs there.
    if vehicle_id and not hub_id:
        vehicle = Vehicle.query.get(vehicle_id)
        if vehicle and vehicle.hub_id:
            hub_id = vehicle.hub_id

    issue = Issue(
        title=title,
        description=description,
        category=category,
        priority=priority,
        status="OPEN",
        reporter_id=reporter_id,
        vehicle_id=vehicle_id,
        driver_id=data.get("driver_id"),
        hub_id=hub_id,
    )
    db.session.add(issue)
    db.session.flush()

    _record_history(issue.id, "status", None, "OPEN", reporter_id)
    _apply_ai_suggestions(issue)
    _apply_similarity_check(issue)
    _apply_impact_assessment(issue)
    _send_creation_notifications(issue)

    db.session.commit()
    return issue


def _apply_ai_suggestions(issue):
    """
    Runs AI classification/priority prediction and stores the results as
    suggestions only (ai_predicted_category / ai_predicted_priority on the
    Issue, plus a full AIPrediction record). The manager-facing `priority`
    and `category` fields are never silently overwritten here — a human
    must accept or override the suggestion explicitly.
    """
    predicted_category, category_confidence = (None, None)
    predicted_priority, priority_confidence = (None, None)

    if category_ready():
        predicted_category, category_confidence = predict_category(issue.title, issue.description)
        issue.ai_predicted_category = predicted_category

    if priority_ready():
        category_for_priority = predicted_category or (issue.category.name if issue.category else "Other")
        predicted_priority, priority_confidence = predict_priority(
            issue.title, issue.description, category_for_priority
        )
        issue.ai_predicted_priority = predicted_priority

    if predicted_category or predicted_priority:
        db.session.add(AIPrediction(
            issue_id=issue.id,
            predicted_category=predicted_category,
            category_confidence=category_confidence,
            predicted_priority=predicted_priority,
            priority_confidence=priority_confidence,
        ))


def _apply_similarity_check(issue):
    """
    Compares the new issue against other currently-open issues and stores any
    matches above the similarity threshold. Never auto-merges — this is
    surfaced to the manager as "potentially related" only.
    """
    candidates = (
        Issue.query
        .filter(Issue.id != issue.id)
        .filter(Issue.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"]))
        .order_by(Issue.created_at.desc())
        .limit(200)
        .all()
    )
    candidate_tuples = [(c.id, c.title, c.description) for c in candidates]
    matches = find_similar_issues(issue.title, issue.description, candidate_tuples)

    for related_id, score in matches:
        db.session.add(SimilarIssue(issue_id=issue.id, related_issue_id=related_id, similarity_score=score))

    if matches:
        notification_service.notify_role(
            "ops_manager",
            f"Potentially related issue(s) found for #{issue.id} \"{issue.title}\".",
            "similarity",
        )


def _apply_impact_assessment(issue):
    level, explanation = impact_service.assess_impact(issue)
    issue.operational_impact = level
    issue.impact_explanation = explanation


def _send_creation_notifications(issue):
    if issue.priority == "Critical":
        notification_service.notify_role(
            "ops_manager",
            f"Critical issue reported: #{issue.id} \"{issue.title}\".",
            "critical_issue",
        )
    if issue.operational_impact in ("HIGH", "CRITICAL"):
        notification_service.notify_role(
            "ops_manager",
            f"Issue #{issue.id} has a potential {issue.operational_impact} operational impact.",
            "impact",
        )


def change_status(issue_id, new_status, changed_by_id):
    issue = Issue.query.get(issue_id)
    if not issue:
        raise IssueServiceError("Issue not found", 404)

    allowed_next = VALID_TRANSITIONS.get(issue.status, set())
    if new_status not in allowed_next:
        raise IssueServiceError(
            f"Cannot move issue from '{issue.status}' to '{new_status}'. "
            f"Allowed next states: {sorted(allowed_next) or 'none'}"
        )

    old_status = issue.status
    issue.status = new_status
    db.session.flush()
    _record_history(issue.id, "status", old_status, new_status, changed_by_id)
    db.session.commit()
    return issue


def change_priority(issue_id, new_priority, changed_by_id, reason=None):
    issue = Issue.query.get(issue_id)
    if not issue:
        raise IssueServiceError("Issue not found", 404)
    if new_priority not in ISSUE_PRIORITIES:
        raise IssueServiceError(f"Priority must be one of {ISSUE_PRIORITIES}")

    old_priority = issue.priority
    issue.priority = new_priority
    if reason:
        issue.priority_override_reason = reason
    db.session.flush()
    _record_history(issue.id, "priority", old_priority, new_priority, changed_by_id)
    db.session.commit()
    return issue


def assign_issue(issue_id, changed_by_id, team_id=None, user_id=None):
    issue = Issue.query.get(issue_id)
    if not issue:
        raise IssueServiceError("Issue not found", 404)

    old_team = issue.assigned_team.name if issue.assigned_team else None
    old_user = issue.assigned_user.name if issue.assigned_user else None

    if team_id is not None:
        issue.assigned_team_id = team_id
    if user_id is not None:
        issue.assigned_user_id = user_id

    if issue.status == "OPEN":
        issue.status = "ASSIGNED"

    db.session.flush()
    new_team = issue.assigned_team.name if issue.assigned_team else None
    new_user = issue.assigned_user.name if issue.assigned_user else None
    _record_history(issue.id, "assignment", f"{old_team}/{old_user}", f"{new_team}/{new_user}", changed_by_id)

    if user_id is not None:
        notification_service.notify_user(
            user_id, f"You have been assigned to issue #{issue.id} \"{issue.title}\".", "assignment"
        )

    db.session.commit()
    return issue


def add_comment(issue_id, user_id, text):
    text = (text or "").strip()
    if not text:
        raise IssueServiceError("Comment cannot be empty")
    issue = Issue.query.get(issue_id)
    if not issue:
        raise IssueServiceError("Issue not found", 404)

    comment = IssueComment(issue_id=issue_id, user_id=user_id, comment=text)
    db.session.add(comment)
    db.session.commit()
    return comment


def _record_history(issue_id, field, old_value, new_value, changed_by_id):
    entry = IssueHistory(
        issue_id=issue_id,
        field_changed=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        changed_by_id=changed_by_id,
    )
    db.session.add(entry)
