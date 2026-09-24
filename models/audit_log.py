from datetime import datetime
from extensions.database import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "LOGIN", "ISSUE_STATUS_CHANGE"
    entity = db.Column(db.String(50))  # e.g. "issue", "vehicle", "user"
    entity_id = db.Column(db.Integer)
    old_value = db.Column(db.String(255))
    new_value = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "user": self.user.name if self.user else "system",
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
