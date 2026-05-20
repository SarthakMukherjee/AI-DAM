import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.sql import func

from app.db.session.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    # PRIMARY ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # WHO RECEIVES IT
    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # WHICH ASSET THIS IS ABOUT
    asset_id = Column(
        String,
        ForeignKey("assets.id"),
        nullable=False
    )

    # NOTIFICATION CONTENT
    message = Column(
        Text,
        nullable=False
    )

    # OPTIONAL REJECTION REASON
    # provided by reviewer, can be null
    reason = Column(
        Text,
        nullable=True
    )

    # READ STATUS
    is_read = Column(
        Boolean,
        default=False
    )

    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )