from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

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

    # ================================================
    # FEATURE 3.3 - Expiry Status (Added on 06-07-26)
    # ================================================

    expired: bool = False

    expiring_soon: bool = False

    days_until_expiry: Optional[int] = None
    # ================================================

    created_at: datetime

    class Config: 
        from_attributes = True

    
    # Duplicate Merge/Replace Workflow
class DuplicateResolveRequest(BaseModel):
    """
    Request payload for resolving duplicate assets.
    
    canonical_asset_id
        Asset that should be kept

    duplicate_asset_id
        Asset that should be retired/deleted.
    
    action
        retire -> Soft delete
        delete -> permanent delete

    merge_metadata 
        Merge AI metadata and business metadata into the canonical asset before movig the duplicate.
    """

    canonical_asset_id:str
    duplicate_asset_id:str

    action: Literal[
        "retire",
        "delete"
    ]

    merge_metadata: bool=True

class DuplicateResolvseResponse(BaseModel):
    """
    Response after duplicate resolution.
    """
    success:bool
    message:str
    canonical_asset_id:str
    duplicate_asset_id:str
    action:str
    metadata_merged:bool