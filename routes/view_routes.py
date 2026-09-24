"""Serves server-rendered HTML pages. All actual data comes from the JSON API via JS."""
from flask import Blueprint, render_template, redirect

view_bp = Blueprint("views", __name__)


@view_bp.route("/")
def index():
    return redirect("/login")


@view_bp.route("/login")
def login_page():
    return render_template("login.html")


@view_bp.route("/issues")
def issues_page():
    return render_template("issues.html")


@view_bp.route("/issues/new")
def create_issue_page():
    return render_template("create_issue.html")


@view_bp.route("/issues/<int:issue_id>")
def issue_details_page(issue_id):
    return render_template("issue_details.html")


@view_bp.route("/vehicles")
def vehicles_page():
    return render_template("vehicles.html")


@view_bp.route("/vehicles/<int:vehicle_id>")
def vehicle_details_page(vehicle_id):
    return render_template("vehicle_details.html")


@view_bp.route("/drivers")
def drivers_page():
    return render_template("drivers.html")


@view_bp.route("/hubs")
def hubs_page():
    return render_template("hubs.html")


@view_bp.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@view_bp.route("/notifications")
def notifications_page():
    return render_template("notifications.html")


@view_bp.route("/audit-logs")
def audit_logs_page():
    return render_template("audit_logs.html")


@view_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@view_bp.route("/users")
def users_page():
    return render_template("users.html")


@view_bp.route("/teams")
def teams_page():
    return render_template("teams.html")


@view_bp.route("/settings")
def settings_page():
    return render_template("settings.html")
