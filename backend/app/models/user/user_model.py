import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime
)

from sqlalchemy.sql import func

from app.db.session.database import Base


class User(Base):
    __tablename__ = "users"

    # PRIMARY ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # IDENTITY
    email = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    full_name = Column(
        String,
        nullable=False
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    # ROLE
    # admin    → upload, manage users, manage assets
    # reviewer → approve/reject drafts, view analytics
    # user     → download/preview approved assets only

    role = Column(
        String,
        nullable=False,
        default="user"
    )

    # STATUS
    is_active = Column(
        Boolean,
        default=True
    )

    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )