import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False, index=True) # e.g. "AI_TAG_ACCEPTED"
    user_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, nullable=True, index=True)
    payload = Column(JSONB, nullable=True) # extra context, like which tag was accepted
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
