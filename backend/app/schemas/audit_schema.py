from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class AuditLogResponse(BaseModel):
    id: str
    asset_id: Optional[str] = None
    user_id: str
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class PaginatedAuditLogs(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[AuditLogResponse]
