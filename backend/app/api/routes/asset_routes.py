from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Form
)

import os
import json

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError


from app.api.dependencies.database import get_db
from app.services.storage.asset_service import AssetService
from app.models.asset.asset_model import Asset
from app.schemas.metadata.metadata_schema import (
    AssetMetadataSchema
)


router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

asset_service = AssetService()


# -----------------------------------
# METADATA SANITIZER
# strips whitespace, newlines, and
# control characters that break
# json.loads when sent via form data
# -----------------------------------

def sanitize_json_string(raw: str) -> str:

    return (
        raw
        .strip()
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )


# -----------------------------------
# UPLOAD
# -----------------------------------

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    status: str = Form("draft"),
    parent_id: str = Form(None),
    db: Session = Depends(get_db)
):

    try:

        sanitized = sanitize_json_string(metadata)

        parsed_metadata = json.loads(sanitized)

        validated_metadata = (
            AssetMetadataSchema(**parsed_metadata)
        )

    except json.JSONDecodeError as json_err:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid JSON in metadata field: "
                f"{str(json_err)}"
            )
        )

    except ValidationError as valid_errors:

        raise HTTPException(
            status_code=422,
            detail=valid_errors.errors()
        )

    except Exception as excep_errors:

        raise HTTPException(
            status_code=500,
            detail=str(excep_errors)
        )

    asset = await asset_service.upload_asset(
        file=file,
        db=db,
        metadata=validated_metadata.model_dump(),
        status=status,
        parent_id=parent_id
    )

    return asset


# -----------------------------------
# DOWNLOAD
# -----------------------------------

@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return FileResponse(
        path=asset.storage_path,
        filename=asset.original_filename
    )


# -----------------------------------
# PREVIEW
# images/videos: returns thumbnail
# PDFs: redirects to /pdf-viewer
# -----------------------------------

@router.get("/{asset_id}/preview")
def preview_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    preview_path = (
        asset.preview_path
        or asset.thumbnail_path
    )

    if not preview_path:
        raise HTTPException(
            status_code=404,
            detail="Preview unavailable"
        )

    return FileResponse(preview_path)


# -----------------------------------
# PDF VIEWER
# serves original PDF inline so the
# browser renders it natively —
# no download required
# -----------------------------------

@router.get("/{asset_id}/pdf-viewer")
def pdf_viewer(
    asset_id: str,
    db: Session = Depends(get_db)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if asset.mime_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Asset is not a PDF"
        )

    if not asset.storage_path or not os.path.exists(
        asset.storage_path
    ):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found on disk"
        )

    # -----------------------------------
    # inline disposition = browser opens
    # attachment disposition = download
    # -----------------------------------

    return FileResponse(
        path=asset.storage_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"inline; filename={asset.original_filename}"
            )
        }
    )


# -----------------------------------
# PDF PAGE IMAGE
# serves a specific page as PNG
# useful for custom page-by-page
# viewers or thumbnails
# -----------------------------------

@router.get("/{asset_id}/pdf-viewer/page/{page_num}")
def pdf_page_image(
    asset_id: str,
    page_num: int,
    db: Session = Depends(get_db)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if asset.mime_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Asset is not a PDF"
        )

    # -----------------------------------
    # PAGE IMAGES ARE STORED AS:
    # previews/{stored_filename}/page_N.png
    # -----------------------------------

    from app.core.config.settings import settings

    page_path = os.path.join(
        settings.STORAGE_PATH,
        "previews",
        asset.stored_filename,
        f"page_{page_num}.png"
    )

    if not os.path.exists(page_path):
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_num} not found"
        )

    return FileResponse(
        path=page_path,
        media_type="image/png"
    )