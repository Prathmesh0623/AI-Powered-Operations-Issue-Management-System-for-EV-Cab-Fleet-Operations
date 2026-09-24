# Import every model so that db.create_all() / Flask-Migrate can discover them.
from models.role import Role
from models.team import Team
from models.user import User
from models.hub import Hub
from models.vehicle import Vehicle
from models.driver import Driver
from models.charging_station import ChargingStation
from models.charging_session import ChargingSession
from models.maintenance import Maintenance
from models.issue_category import IssueCategory
from models.issue import Issue
from models.issue_history import IssueHistory
from models.issue_comment import IssueComment
from models.ai_prediction import AIPrediction
from models.similar_issue import SimilarIssue
from models.notification import Notification
from models.audit_log import AuditLog
