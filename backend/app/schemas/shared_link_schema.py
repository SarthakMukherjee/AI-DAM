from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SharedLinkCreate(BaseModel):
    asset_id: str
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    password: Optional[str] = Field(None, min_length=4)

class SharedLinkResponse(BaseModel):
    id: str
    token: str
    asset_id: str
    created_by: Optional[str]
    expires_at: Optional[datetime]
    has_password: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SharedLinkAccessRequest(BaseModel):
    password: Optional[str] = None
