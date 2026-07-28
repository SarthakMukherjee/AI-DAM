import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from app.db.session.database import Base

class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String, nullable=False, index=True)
    search_type = Column(String, nullable=False)  # 'semantic' or 'hybrid'
    results_count = Column(Integer, nullable=False, default=0)
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Telemetry metrics (Sharper POC Metrics)
    successful_click_asset_id = Column(String, nullable=True)
    time_to_click_ms = Column(Integer, nullable=True)

