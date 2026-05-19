import uuid

from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    Boolean, 
    ForeignKey
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

    file_hash = Column(String, nullable=False, unique=False) # made changes on 18-05-26

    # STORAGE
    storage_path = Column(String)

    thumbnail_path = Column(String, nullable=True)
    preview_path = Column(String, nullable=True)

    # BUSINESS METADATA
    asset_metadata = Column(JSONB, nullable=True)

    # WORKFLOW STATUS
    status = Column(String, default="draft")

    # VERSIONING
    version = Column(Integer, default=1)
    parent_id = Column(String, ForeignKey("assets.id"), nullable=True)
    root_asset_id = Column(String, nullable=True) # new column added on 15-05-26
    is_latest = Column(Boolean, default=True)

    # ARCHIVAL
    is_archived = Column(Boolean, default=False)

    #TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now())