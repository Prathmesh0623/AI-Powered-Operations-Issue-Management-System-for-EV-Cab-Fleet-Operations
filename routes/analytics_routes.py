from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from extensions.database import db
from models.issue import Issue
from models.vehicle import Vehicle
from models.hub import Hub

analytics_bp = Blueprint("analytics", __name__)


def _apply_common_filters(query, args):
    start = args.get("start_date")
    end = args.get("end_date")
    hub_id = args.get("hub_id")
    category = args.get("category")
    priority = args.get("priority")
    status = args.get("status")
    vehicle_id = args.get("vehicle_id")

    if start:
        query = query.filter(Issue.created_at >= start)
    if end:
        query = query.filter(Issue.created_at <= end)
    if hub_id:
        query = query.filter(Issue.hub_id == hub_id)
    if priority:
        query = query.filter(Issue.priority == priority)
    if status:
        query = query.filter(Issue.status == status)
    if vehicle_id:
        query = query.filter(Issue.vehicle_id == vehicle_id)
    if category:
        query = query.join(Issue.category).filter_by(name=category)
    return query


@analytics_bp.route("/overview", methods=["GET"])
@jwt_required()
def overview():
    total = Issue.query.count()
    open_count = Issue.query.filter(Issue.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"])).count()
    critical = Issue.query.filter_by(priority="Critical").count()
    high = Issue.query.filter_by(priority="High").count()
    resolved = Issue.query.filter(Issue.status.in_(["RESOLVED", "CLOSED"])).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    created_today = Issue.query.filter(Issue.created_at >= today_start).count()

    # Average resolution time in hours, for issues that reached RESOLVED/CLOSED.
    resolved_issues = Issue.query.filter(Issue.status.in_(["RESOLVED", "CLOSED"])).all()
    if resolved_issues:
        durations = [(i.updated_at - i.created_at).total_seconds() / 3600 for i in resolved_issues]
        avg_resolution_hours = round(sum(durations) / len(durations), 1)
    else:
        avg_resolution_hours = None

    high_impact = Issue.query.filter(Issue.operational_impact.in_(["HIGH", "CRITICAL"])).count()

    return jsonify({
        "success": True,
        "message": "OK",
        "data": {
            "total_issues": total,
            "open_issues": open_count,
            "critical_issues": critical,
            "high_priority_issues": high,
            "resolved_issues": resolved,
            "created_today": created_today,
            "avg_resolution_time_hours": avg_resolution_hours,
            "potential_high_impact_issues": high_impact,
        }
    }), 200


@analytics_bp.route("/issues", methods=["GET"])
@jwt_required()
def issues_breakdown():
    base_query = _apply_common_filters(Issue.query, request.args)

    by_category = dict(
        db.session.query(func.coalesce(Issue.ai_predicted_category, "Uncategorized"), func.count(Issue.id))
        .group_by(func.coalesce(Issue.ai_predicted_category, "Uncategorized")).all()
    )
    by_priority = dict(db.session.query(Issue.priority, func.count(Issue.id)).group_by(Issue.priority).all())
    by_status = dict(db.session.query(Issue.status, func.count(Issue.id)).group_by(Issue.status).all())

    by_hub_rows = (
        db.session.query(Hub.name, func.count(Issue.id))
        .join(Issue, Issue.hub_id == Hub.id)
        .group_by(Hub.name).all()
    )
    by_hub = dict(by_hub_rows)

    # Daily trend for the last 30 days.
    since = datetime.utcnow() - timedelta(days=30)
    trend_rows = (
        db.session.query(func.date(Issue.created_at), func.count(Issue.id))
        .filter(Issue.created_at >= since)
        .group_by(func.date(Issue.created_at))
        .order_by(func.date(Issue.created_at))
        .all()
    )
    trend = [{"date": str(d), "count": c} for d, c in trend_rows]

    return jsonify({
        "success": True,
        "message": "OK",
        "data": {
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
            "by_hub": by_hub,
            "trend_last_30_days": trend,
        }
    }), 200


@analytics_bp.route("/vehicles", methods=["GET"])
@jwt_required()
def vehicles_analytics():
    rows = (
        db.session.query(Vehicle.registration_number, func.count(Issue.id))
        .join(Issue, Issue.vehicle_id == Vehicle.id)
        .group_by(Vehicle.registration_number)
        .order_by(func.count(Issue.id).desc())
        .limit(10)
        .all()
    )
    top_vehicles_by_issues = [{"vehicle": v, "issue_count": c} for v, c in rows]

    by_status = dict(db.session.query(Vehicle.status, func.count(Vehicle.id)).group_by(Vehicle.status).all())

    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"top_vehicles_by_issue_count": top_vehicles_by_issues, "vehicles_by_status": by_status}
    }), 200


@analytics_bp.route("/hubs", methods=["GET"])
@jwt_required()
def hubs_analytics():
    rows = (
        db.session.query(Hub.name, func.count(Issue.id))
        .join(Issue, Issue.hub_id == Hub.id)
        .group_by(Hub.name)
        .all()
    )
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"issues_by_hub": [{"hub": h, "issue_count": c} for h, c in rows]}
    }), 200


@analytics_bp.route("/recurring-issues", methods=["GET"])
@jwt_required()
def recurring_issues():
    """
    Flags vehicles with a rising or elevated count of issues in the same
    category over the recent window. This surfaces a pattern for a human to
    investigate — it never claims to identify the root cause.
    """
    window_days = request.args.get("window_days", 30, type=int)
    min_occurrences = request.args.get("min_occurrences", 3, type=int)
    since = datetime.utcnow() - timedelta(days=window_days)

    rows = (
        db.session.query(
            Issue.vehicle_id,
            func.coalesce(Issue.ai_predicted_category, "Uncategorized"),
            func.count(Issue.id)
        )
        .filter(Issue.created_at >= since, Issue.vehicle_id.isnot(None))
        .group_by(Issue.vehicle_id, func.coalesce(Issue.ai_predicted_category, "Uncategorized"))
        .having(func.count(Issue.id) >= min_occurrences)
        .all()
    )

    results = []
    for vehicle_id, category, count in rows:
        vehicle = Vehicle.query.get(vehicle_id)
        results.append({
            "vehicle": vehicle.registration_number if vehicle else None,
            "category": category,
            "occurrences": count,
            "window_days": window_days,
        })

    return jsonify({"success": True, "message": "OK", "data": results}), 200
