import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.session.database import Base

class AssetPlacement(Base):
    __tablename__ = "asset_placements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False, index=True)
    platform = Column(String)  # e.g., 'Website', 'HubSpot Email', 'LinkedIn Ad'
    placement_url_or_id = Column(String)
    added_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
