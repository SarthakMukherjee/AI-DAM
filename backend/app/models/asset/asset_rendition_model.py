import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session.database import Base

class AssetRendition(Base):
    __tablename__ = "asset_renditions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # e.g., "web-compressed", "thumbnail", "social-1080x1080"
    rendition_name = Column(String, nullable=False)
    
    storage_path = Column(String, nullable=False)
    mime_type = Column(String)
    file_size = Column(Integer)
    
    # Optional dimension tracking
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
