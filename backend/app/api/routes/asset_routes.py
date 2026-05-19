from fastapi import (
    APIRouter, 
    UploadFile,
    File,
    Depends,
    HTTPException,
    Form
)

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

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    status: str = Form("draft"),
    parent_id:str = Form(None),
    db: Session = Depends(get_db)
):
    

    try:
        parsed_metadata = json.loads(metadata)
        validated_metadata = (
            AssetMetadataSchema(**parsed_metadata)
        )

    except ValidationError as valid_errors:
        raise HTTPException(
            status_code=400,
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

@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(404, detail="Asset not found")
    
    return FileResponse(
        path=asset.storage_path,
        filename=asset.original_filename
        )

@router.get("/{asset_id}/preview")
def preview_asset(
    asset_id: str, 
    db:Session=Depends(get_db)
    ):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(404, detail="Asset not found")
    
    preview_path = asset.preview_path or asset.thumbnail_path

    if not preview_path:
        raise HTTPException(404, detail="Preview Unavailable")
    
    return FileResponse(preview_path)