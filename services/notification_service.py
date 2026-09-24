from extensions.database import db
from models.notification import Notification
from models.user import User


def notify_user(user_id, message, notif_type):
    notif = Notification(user_id=user_id, message=message, type=notif_type)
    db.session.add(notif)
    return notif


def notify_role(role_name, message, notif_type):
    """Notify every active user with a given role (e.g. all ops_managers)."""
    users = User.query.join(User.role).filter_by(name=role_name).filter(User.is_active.is_(True)).all()
    for user in users:
        notify_user(user.id, message, notif_type)
