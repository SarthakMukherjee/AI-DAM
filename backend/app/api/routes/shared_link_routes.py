from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import get_current_user
from app.schemas.user.schemas import UserResponse
from app.schemas.shared_link_schema import SharedLinkCreate, SharedLinkResponse, SharedLinkAccessRequest
from app.services.asset.shared_link_service import SharedLinkService
from app.models.asset.shared_link_model import SharedLink

router = APIRouter(prefix="/shared-links", tags=["Shared Links"])

def _format_link_response(link: SharedLink) -> SharedLinkResponse:
    return SharedLinkResponse(
        id=link.id,
        token=link.token,
        asset_id=link.asset_id,
        created_by=link.created_by,
        expires_at=link.expires_at,
        has_password=bool(link.password_hash),
        created_at=link.created_at
    )

@router.post("/", response_model=SharedLinkResponse)
def create_shared_link(
    req: SharedLinkCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new shared link for an asset.
    """
    link = SharedLinkService.create_link(db, req, current_user.id)
    return _format_link_response(link)

@router.get("/{token}")
def get_shared_link_info(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get info about a shared link before attempting to access it (e.g. check if it needs a password).
    """
    link = SharedLinkService.get_link_by_token(db, token)
    return {
        "asset_id": link.asset_id,
        "has_password": bool(link.password_hash),
        "expires_at": link.expires_at
    }

@router.post("/{token}/access")
def access_shared_link(
    token: str,
    req: SharedLinkAccessRequest,
    db: Session = Depends(get_db)
):
    """
    Access a shared link. If password protected, must provide valid password.
    Returns asset metadata and preview/download paths.
    """
    link = SharedLinkService.get_link_by_token(db, token)
    
    if not SharedLinkService.verify_password(link, req.password):
        raise HTTPException(status_code=401, detail="Invalid password")
        
    asset = link.asset
    return {
        "asset_id": asset.id,
        "original_filename": asset.original_filename,
        "mime_type": asset.mime_type,
        "preview_path": asset.preview_path,
        "thumbnail_path": asset.thumbnail_path,
        "storage_path": asset.storage_path, # In a real app we'd generate a signed URL here
        "asset_metadata": asset.asset_metadata
    }
