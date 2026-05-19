from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AssetCreateSchema(BaseModel):
    asset_metadata: Optional[dict] = None
    status: Optional[str] = "draft"
    parent_id: Optional[str] = None


class AssetResponse(BaseModel):
    id: str

    original_filename: str

    mime_type: str

    file_size: int

    metadata: Optional[dict]

    status: str

    version: int

    parent_id: Optional[str]

    is_latest: bool

    is_archived: bool

    thumbnail_path: Optional[str]

    preview_path: Optional[str]

    created_at: datetime

    class Config: 
        from_attributes = True
