import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer
)

from sqlalchemy.sql import func

from app.db.session.database import Base


class AssetUsage(Base):
    __tablename__ = "asset_usage"

    # PRIMARY ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # REFERENCES
    asset_id = Column(
        String,
        ForeignKey("assets.id"),
        nullable=False,
        index=True
    )

    # ACTION TYPE
    # download / preview / search
    action = Column(
        String,
        nullable=False
    )

    # TOTAL USAGE COUNT
    # incremented on every action
    usage_count = Column(
        Integer,
        default=1,
        nullable=False
    )

    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )