from datetime import datetime
from extensions.database import db


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship("User", back_populates="team")
    assigned_issues = db.relationship("Issue", back_populates="assigned_team")

    def __repr__(self):
        return f"<Team {self.name}>"
