import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime
)

from sqlalchemy.dialects.postgresql import ARRAY
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

    # ROLE — all supported roles:
    # super_admin      → full system access
    # admin            → upload, manage assets, manage users
    # reviewer         → approve/reject/publish/restrict assets
    # marketing_manager→ upload, view all approved, manage campaigns
    # designer         → upload, view all approved assets
    # content_lead     → upload, curate content, view analytics
    # sales_user       → view approved assets, download for sales use
    # website_team     → upload & manage website-safe assets
    # external_partner → restricted view of approved assets only
    # user             → browse & download approved assets only

    role = Column(
        String,
        nullable=False,
        default="user"
    )

    # DOMAIN-SCOPED ACCESS
    # if set, user only sees assets whose business.domain is in this list
    # null = no restriction (sees all domains)
    allowed_domains = Column(
        ARRAY(String),
        nullable=True
    )

    # STATUS
    is_active = Column(
        Boolean,
        default=True
    )

    # Time-limited access for external partners or contractors (Phase 4.2)
    access_expiry = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # TIMESTAMPS
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )