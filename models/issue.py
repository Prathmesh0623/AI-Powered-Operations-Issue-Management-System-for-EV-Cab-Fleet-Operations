from datetime import datetime
from extensions.database import db

ISSUE_STATUSES = ("OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED")
ISSUE_PRIORITIES = ("Low", "Medium", "High", "Critical")

# Which status transitions are allowed. Enforced in issue_service, not just documented here.
VALID_TRANSITIONS = {
    "OPEN": {"ASSIGNED", "REJECTED"},
    "ASSIGNED": {"IN_PROGRESS", "OPEN"},
    "IN_PROGRESS": {"RESOLVED", "ASSIGNED"},
    "RESOLVED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": set(),
    "REJECTED": set(),
}


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("issue_categories.id"), nullable=True)
    priority = db.Column(db.String(20), default="Medium", nullable=False)
    status = db.Column(db.String(20), default="OPEN", nullable=False)

    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True)
    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=True)

    # AI predicted vs manager-confirmed values, kept separately for transparency.
    ai_predicted_category = db.Column(db.String(100), nullable=True)
    ai_predicted_priority = db.Column(db.String(20), nullable=True)
    priority_override_reason = db.Column(db.String(255), nullable=True)

    # Rule-based operational impact assessment (Phase 10), transparent by design — never an ML black box.
    operational_impact = db.Column(db.String(20), nullable=True)  # LOW / MEDIUM / HIGH / CRITICAL
    impact_explanation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("IssueCategory", back_populates="issues")
    reporter = db.relationship("User", foreign_keys=[reporter_id])
    assigned_user = db.relationship("User", foreign_keys=[assigned_user_id])
    assigned_team = db.relationship("Team", back_populates="assigned_issues")
    vehicle = db.relationship("Vehicle", back_populates="issues")
    driver = db.relationship("Driver", back_populates="issues")
    hub = db.relationship("Hub", back_populates="issues")

    history = db.relationship("IssueHistory", back_populates="issue", cascade="all, delete-orphan")
    comments = db.relationship("IssueComment", back_populates="issue", cascade="all, delete-orphan")
    maintenance_records = db.relationship("Maintenance", back_populates="issue")
    ai_predictions = db.relationship("AIPrediction", back_populates="issue", cascade="all, delete-orphan")
    similar_issues_found = db.relationship(
        "SimilarIssue", foreign_keys="SimilarIssue.issue_id", overlaps="issue", viewonly=True
    )

    def to_dict(self, include_details=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.name if self.category else self.ai_predicted_category,
            "priority": self.priority,
            "status": self.status,
            "reporter": self.reporter.name if self.reporter else None,
            "assigned_team": self.assigned_team.name if self.assigned_team else None,
            "assigned_user": self.assigned_user.name if self.assigned_user else None,
            "vehicle": self.vehicle.registration_number if self.vehicle else None,
            "hub": self.hub.name if self.hub else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details:
            data.update({
                "ai_predicted_category": self.ai_predicted_category,
                "ai_predicted_priority": self.ai_predicted_priority,
                "priority_override_reason": self.priority_override_reason,
                "operational_impact": self.operational_impact,
                "impact_explanation": self.impact_explanation,
                "similar_issues": [s.to_dict() for s in self.similar_issues_found],
                "driver": self.driver.name if self.driver else None,
                "comments": [c.to_dict() for c in self.comments],
                "history": [h.to_dict() for h in self.history],
            })
        return data
