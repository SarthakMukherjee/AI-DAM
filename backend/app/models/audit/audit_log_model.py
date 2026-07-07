import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime
)

from sqlalchemy.sql import func

from app.db.session.database import Base


class AuditLog(Base):
    __tablename__="audit_logs"

    # Primary ID
    id = Column(String, primary_key=True, default=lambda:str(uuid.uuid4()))

    # Audit Target
    # Related asset (optional)
    asset_id=Column(String, nullable=True, index=True)

    # Actor (Required)
    user_id=Column(String, nullable=False, index=True)

    # Action Details
    # Examples:
    # UPLOAD
    # APPROVE
    # REJECT
    # DELETE
    # ROLE_CHANGE
    # UPDATE_METADATA
    action=Column(String, nullable=False, index=True)

    # Optional metadata field affected
    field_name=Column(String, nullable=True)

    old_value=Column(Text, nullable=True)

    new_value=Column(Text, nullable=True)

    # Request Context
    ip_address=Column(String, nullable=True)

    # Timestamp
    timestamp=Column(DateTime(timezone=True),
                     server_default=func.now(),
                     index=True
                     )
    
    