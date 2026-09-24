from datetime import datetime
from extensions.database import db


class IssueHistory(db.Model):
    __tablename__ = "issue_history"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    field_changed = db.Column(db.String(50), nullable=False)  # e.g. "status", "priority", "assigned_team"
    old_value = db.Column(db.String(255))
    new_value = db.Column(db.String(255))
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    issue = db.relationship("Issue", back_populates="history")
    changed_by = db.relationship("User")

    def to_dict(self):
        return {
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by.name if self.changed_by else "system",
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
