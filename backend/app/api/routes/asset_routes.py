from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Form,
    Request,
    status
)

import os
import json

from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import (
    get_current_user,
    require_admin
)
from app.services.storage.asset_service import AssetService
from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage
from app.models.user.user_model import User
from app.schemas.metadata.metadata_schema import AssetMetadataSchema


limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

asset_service = AssetService()


def sanitize_json_string(raw: str) -> str:
    return (
        raw.strip()
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )


def log_usage(asset_id: str, action: str, db: Session):
    try:
        usage = AssetUsage(asset_id=asset_id, action=action, usage_count=1)
        db.add(usage)
        db.commit()
    except Exception as e:
        print(f"Usage logging failed: {e}")


def is_cloud_url(path: str) -> bool:
    """Check if path is a cloud URL rather than local path."""
    return path and (
        path.startswith("https://") or
        path.startswith("http://")
    )


# -----------------------------------
# UPLOAD — admin only
# -----------------------------------

@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    parent_id: str = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    try:
        sanitized = sanitize_json_string(metadata)
        parsed_metadata = json.loads(sanitized)
        validated_metadata = AssetMetadataSchema(**parsed_metadata)

    except json.JSONDecodeError as json_err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in metadata: {str(json_err)}")
    except ValidationError as valid_errors:
        raise HTTPException(status_code=422, detail=valid_errors.errors())
    except Exception as excep_errors:
        raise HTTPException(status_code=500, detail=str(excep_errors))

    asset = await asset_service.upload_asset(
        file=file,
        db=db,
        metadata=validated_metadata.model_dump(),
        status="draft",
        parent_id=parent_id
    )

    return asset


# -----------------------------------
# LIST ASSETS
# -----------------------------------

@router.get("/")
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "user":
        return (
            db.query(Asset)
            .filter(
                Asset.status == "approved",
                Asset.is_latest == True
            )
            .all()
        )

    return db.query(Asset).all()


# -----------------------------------
# DOWNLOAD
# redirects to cloud URL or serves local
# -----------------------------------

@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if (
        current_user.role == "user"
        and (asset.status != "approved" or not asset.is_latest)
    ):
        raise HTTPException(status_code=403, detail="Asset not available")

    log_usage(asset_id, "download", db)

    # cloud URL — redirect browser directly
    if is_cloud_url(asset.storage_path):
        return RedirectResponse(url=asset.storage_path)

    # local file — serve directly
    return FileResponse(
        path=asset.storage_path,
        filename=asset.original_filename
    )


# -----------------------------------
# PREVIEW
# redirects to cloud URL or serves local
# -----------------------------------

@router.get("/{asset_id}/preview")
def preview_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if current_user.role == "user" and asset.status != "approved":
        raise HTTPException(status_code=403, detail="Asset not available")

    preview_path = asset.preview_path or asset.thumbnail_path

    if not preview_path:
        raise HTTPException(status_code=404, detail="Preview unavailable")

    log_usage(asset_id, "preview", db)

    # cloud URL — redirect
    if is_cloud_url(preview_path):
        return RedirectResponse(url=preview_path)

    # local file
    return FileResponse(preview_path)


# -----------------------------------
# PDF VIEWER
# -----------------------------------

@router.get("/{asset_id}/pdf-viewer")
def pdf_viewer(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if current_user.role == "user" and asset.status != "approved":
        raise HTTPException(status_code=403, detail="Asset not available")

    if asset.mime_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Asset is not a PDF")

    log_usage(asset_id, "preview", db)

    # cloud URL — redirect so browser opens PDF natively
    if is_cloud_url(asset.storage_path):
        return RedirectResponse(url=asset.storage_path)

    if not asset.storage_path or not os.path.exists(asset.storage_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=asset.storage_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={asset.original_filename}"
        }
    )


# -----------------------------------
# PDF PAGE IMAGE
# -----------------------------------

@router.get("/{asset_id}/pdf-viewer/page/{page_num}")
def pdf_page_image(
    asset_id: str,
    page_num: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if current_user.role == "user" and asset.status != "approved":
        raise HTTPException(status_code=403, detail="Asset not available")

    if asset.mime_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Asset is not a PDF")

    # for cloud stored PDFs, preview_path already points to page 1 cloud URL
    if is_cloud_url(asset.preview_path) and page_num == 1:
        return RedirectResponse(url=asset.preview_path)

    from app.core.config.settings import settings

    page_path = os.path.join(
        settings.STORAGE_PATH,
        "previews",
        asset.stored_filename,
        f"page_{page_num}.png"
    )

    if not os.path.exists(page_path):
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found")

    return FileResponse(path=page_path, media_type="image/png")