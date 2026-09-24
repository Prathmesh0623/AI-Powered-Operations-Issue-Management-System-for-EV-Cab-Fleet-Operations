from datetime import datetime
from extensions.database import db


class AIPrediction(db.Model):
    __tablename__ = "ai_predictions"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)

    predicted_category = db.Column(db.String(100))
    category_confidence = db.Column(db.Float)
    predicted_priority = db.Column(db.String(20))
    priority_confidence = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    issue = db.relationship("Issue", back_populates="ai_predictions")

    def to_dict(self):
        return {
            "predicted_category": self.predicted_category,
            "category_confidence": self.category_confidence,
            "predicted_priority": self.predicted_priority,
            "priority_confidence": self.priority_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
