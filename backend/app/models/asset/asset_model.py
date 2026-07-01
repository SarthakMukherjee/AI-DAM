import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.session.database import Base


class Asset(Base):
    __tablename__ = "assets"

    # PRIMARY ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # ORIGINAL FILE DETAILS
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)

    mime_type = Column(String)
    file_size = Column(Integer)

    file_hash = Column(String, nullable=False, unique=False)

    # STORAGE
    storage_path = Column(String)

    thumbnail_path = Column(String, nullable=True)
    preview_path = Column(String, nullable=True)

    # BUSINESS METADATA (nested JSONB — legacy / upload payload)
    asset_metadata = Column(JSONB, nullable=True)

    # WORKFLOW STATUS
    status = Column(String, default="draft")

    # VERSIONING
    version = Column(Integer, default=1)
    parent_id = Column(String, ForeignKey("assets.id"), nullable=True)
    root_asset_id = Column(String, nullable=True)
    is_latest = Column(Boolean, default=True)

    # ARCHIVAL
    is_archived = Column(Boolean, default=False)

    # -------------------------------------------------------
    # AI RETRIEVAL — queryable individual columns
    # (duplicated out of asset_metadata.ai_enrichment for
    #  direct SQL filtering, indexing, and completeness checks)
    # -------------------------------------------------------

    # Near-duplicate detection: 16-char hex dHash fingerprint (images only)
    perceptual_hash = Column(String(16), nullable=True)

    # Clean LLM-generated 1-2 sentence summary of the asset
    ai_summary = Column(Text, nullable=True)

    # Metadata completeness score 0-100
    completeness_score = Column(Integer, default=0)

    # Queryable AI enrichment fields
    ai_tags = Column(JSONB, nullable=True)           # list[str]
    detected_objects = Column(JSONB, nullable=True)  # list[str]
    extracted_text = Column(Text, nullable=True)
    image_caption = Column(Text, nullable=True)

    # -------------------------------------------------------
    # VERSION CONTROL — changelog
    # -------------------------------------------------------

    # Human-readable description of what changed in this version
    changelog = Column(Text, nullable=True)

    # Username / user_id of whoever uploaded this version
    updated_by = Column(String, nullable=True)

    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )