from extensions.database import db
from models.audit_log import AuditLog


def log_action(user_id, action, entity=None, entity_id=None, old_value=None, new_value=None):
    """Record a sensitive action. Never log passwords, tokens, or secrets here."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
