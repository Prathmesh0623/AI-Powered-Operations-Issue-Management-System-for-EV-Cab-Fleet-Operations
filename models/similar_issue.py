from datetime import datetime
from extensions.database import db


class SimilarIssue(db.Model):
    __tablename__ = "similar_issues"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    related_issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    issue = db.relationship("Issue", foreign_keys=[issue_id])
    related_issue = db.relationship("Issue", foreign_keys=[related_issue_id])

    def to_dict(self):
        return {
            "related_issue_id": self.related_issue_id,
            "related_issue_title": self.related_issue.title if self.related_issue else None,
            "similarity_score": round(self.similarity_score * 100, 1),
        }
