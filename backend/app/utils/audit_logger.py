from sqlalchemy.orm import Session
from app.models.audit.audit_log_model import AuditLog

def log_audit_event(
        db:Session,
        *,
        user_id:str,
        action:str,
        asset_id:str | None=None,
        field_name:str | None=None,
        old_value:str | None=None,
        new_value:str | None=None,
        ip_address:str | None=None,
) -> AuditLog:
    """
    Record a single audit event.

    Notes:
    - Uses the caller's active SQLAlchemy session.
    - Does NOT commit or rollback.
    - Safe to call inside existing transactions.
    """

    audit=AuditLog(
        user_id=user_id,
        asset_id=asset_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
        )
    
    db.add(audit)

    # Assign primary key immediately if needed
    db.flush()

    return audit