from extensions.database import db


class IssueCategory(db.Model):
    __tablename__ = "issue_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    issues = db.relationship("Issue", back_populates="category")

    def __repr__(self):
        return f"<IssueCategory {self.name}>"
