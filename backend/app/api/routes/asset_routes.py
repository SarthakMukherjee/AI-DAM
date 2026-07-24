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
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import (
    get_current_user,
    require_admin,
    require_upload_permission
)
from app.services.storage.asset_service import AssetService
from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage
from app.models.user.user_model import User
from app.schemas.metadata.metadata_schema import AssetMetadataSchema
from app.services.storage.storage_service import StorageService
from app.ai.tagging.auto_tagging_service import AutoTaggingService
from app.utils.image_hash import (
    hamming_distance,
    similarity_score,
    NEAR_DUPLICATE_THRESHOLD_DISTANCE,
    VISUAL_SIMILARITY_MIN_SCORE,
)
from app.schemas.asset_schema import (
    DuplicateResolveRequest,
    DuplicateResolveResponse,
    AssetPlacementCreate,
    AssetPlacementResponse,
    AssetBulkEditRequest
)
from app.models.asset.asset_placement_model import AssetPlacement
from app.services.storage.duplicate_merge_service import (
    DuplicateMergeService
)

from app.services.storage.expiry_service import ExpiryService
from app.utils.audit_logger import log_audit_event




limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

asset_service = AssetService()


def check_restricted_access(asset: Asset, user: User) -> None:
    """Enforces asset-level access restrictions for restricted status (Phase 4.1)."""
    if asset.status == "restricted":
        if user.role not in ["super_admin", "admin"]:
            meta = asset.asset_metadata or {}
            gov = meta.get("governance") or {}
            allowed_roles = gov.get("restricted_to_roles") or ["admin", "reviewer", "super_admin"]
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: this asset is restricted to specific roles"
                )



def _validate_asset_type_rules(metadata) -> None:
    """
    Phase 1.2 — Per-asset-class conditional metadata validation.
    Called after Pydantic schema validation on every upload.
    Raises HTTP 422 with a clear message if a rule is violated.
    """
    mand = metadata.mandatory
    biz  = metadata.business
    asset_type = mand.asset_type.value if hasattr(mand.asset_type, "value") else str(mand.asset_type)

    errors = []

    if asset_type in ("video", "social_creative"):
        # Videos and social creatives must have at minimum a campaign OR service_line
        if not biz.campaign and not biz.service_line:
            errors.append(
                f"Asset type '{asset_type}' requires either 'campaign' or 'service_line' "
                "in the business metadata section."
            )

    if asset_type in ("brochure", "campaign_file"):
        # Brochures and campaign files must have BOTH campaign and service_line
        if not biz.campaign:
            errors.append(f"Asset type '{asset_type}' requires 'campaign' in business metadata.")
        if not biz.service_line:
            errors.append(f"Asset type '{asset_type}' requires 'service_line' in business metadata.")

    if asset_type == "pitch_deck":
        # Pitch decks must specify target audience and use case
        if not biz.audience:
            errors.append("Asset type 'pitch_deck' requires 'audience' in business metadata.")
        if not biz.use_case:
            errors.append("Asset type 'pitch_deck' requires 'use_case' in business metadata.")

    if asset_type in ("logo", "brand_guideline"):
        # Logos and brand guidelines must be assigned to a domain
        if not biz.domain:
            errors.append(f"Asset type '{asset_type}' requires 'domain' in business metadata.")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"asset_type_validation_errors": errors}
        )


def sanitize_json_string(raw: str) -> str:
    return (
        raw.strip()
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )


def log_usage(asset_id: str, action: str, db: Session, user_id: str | None = None):
    try:
        usage = AssetUsage(
            asset_id=asset_id,
            action=action,
            usage_count=1,
            user_id=user_id,
        )
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
    changelog: str = Form(None),
    # Phase 6.4 — Video-specific optional fields
    video_duration_seconds: int = Form(None),
    video_transcript: str = Form(None),
    video_aspect_ratio: str = Form(None),
    
    # Phase 1.2 — Governance fields
    geographic_restrictions: str = Form(None),
    platform_restrictions: str = Form(None),
    source_ownership: str = Form(None),
    model_release_status: str = Form("Not Required"),
    
    # Phase 2 - Relationships
    relationship_type: str = Form("master"),

    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    # Phase 1.2 — per-asset-class metadata rules
    _validate_asset_type_rules(validated_metadata)

    asset = await asset_service.upload_asset(
        file=file,
        db=db,
        metadata=validated_metadata.model_dump(),
        status="draft",
        parent_id=parent_id,
        relationship_type=relationship_type,
        changelog=changelog,
        uploaded_by=current_user.email if hasattr(current_user, "email") else str(current_user.id),
    )

    # Phase 6.4 — Persist video-specific fields if provided
    if video_duration_seconds is not None:
        asset.video_duration_seconds = video_duration_seconds
    if video_transcript:
        asset.video_transcript = video_transcript.strip()
    if video_aspect_ratio:
        asset.video_aspect_ratio = video_aspect_ratio.strip()
        
    # Phase 1.2 — Persist Governance fields
    if geographic_restrictions:
        try:
            asset.geographic_restrictions = json.loads(geographic_restrictions)
        except:
            pass
    if platform_restrictions:
        try:
            asset.platform_restrictions = json.loads(platform_restrictions)
        except:
            pass
    if source_ownership:
        asset.source_ownership = source_ownership.strip()
    if model_release_status:
        asset.model_release_status = model_release_status.strip()

    if any([video_duration_seconds, video_transcript, video_aspect_ratio, geographic_restrictions, platform_restrictions, source_ownership, model_release_status]):
        db.add(asset)
        db.commit()
        db.refresh(asset)

    # Log UPLOAD audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="UPLOAD",
        asset_id=asset.id,
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return asset

# Written on 30-06-26
# -----------------------------------
# ANALYZE — admin only
# -----------------------------------

@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze_asset(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    temp_path = None
    storage_service = StorageService()
    try:
        # Save file to temp location
        filename, temp_path, _ = await storage_service.save_to_temp(file)

        # Call suggestion logic in AutoTaggingService
        auto_tagger = AutoTaggingService()
        file_extension = filename.split(".")[-1].lower()
        suggestions = auto_tagger.suggest_metadata(
            asset_type=file_extension,
            file_path=temp_path,
            filename=file.filename
        )

        # Clean up temp file
        storage_service.delete_temp_file(temp_path)
        return suggestions

    except Exception as excep_errors:
        if temp_path:
            storage_service.delete_temp_file(temp_path)
        raise HTTPException(status_code=500, detail=str(excep_errors))
# END

# -----------------------------------
# LIST ASSETS
# -----------------------------------

@router.get("/")
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Roles that only see approved + latest assets
    RESTRICTED_VIEW_ROLES = ["user", "sales_user", "external_partner"]

    query = db.query(Asset)

    if current_user.role in RESTRICTED_VIEW_ROLES:
        query = query.filter(
            Asset.status == "approved",
            Asset.is_latest == True,
            Asset.is_archived == False
        )
    else:
        # All other content team / admin roles see everything
        query = query.filter(Asset.is_archived == False)

    # Filter out restricted assets if user is not in the allowed roles list (Phase 4.1)
    if current_user.role not in ["super_admin", "admin"]:
        role_containment = Asset.asset_metadata["governance"]["restricted_to_roles"].contains([current_user.role])
        query = query.filter(or_(Asset.status != "restricted", role_containment))

    # Domain-scoped access: if user has domain restriction, filter assets
    if current_user.allowed_domains:
      # Filter by business.domain inside JSONB
      domain_filter = Asset.asset_metadata[
        "business"
      ]["domain"].as_string().in_(current_user.allowed_domains)
      query = query.filter(domain_filter)

    assets = query.all()

    response = []

    for asset in assets:

        # Automatically restrict expired assets
        ExpiryService.auto_restrict_if_expired(asset=asset, db=db)
        expiry=ExpiryService.build_expiry_status(asset)

        response.append(
            {
                **asset.__dict__,
                "metadata":asset.asset_metadata,
                **expiry,
            }
        )

    return response


# -----------------------------------
# SUBMIT FOR REVIEW — content team
# moves asset from draft to pending_review
# -----------------------------------

@router.patch("/{asset_id}/submit-for-review")
def submit_for_review(
    asset_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    SUBMIT_ROLES = [
        "super_admin", "admin",
        "marketing_manager", "designer", "content_lead", "website_team"
    ]

    if current_user.role not in SUBMIT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit assets for review"
        )

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.status not in ["draft", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit for review. Current status: {asset.status}"
        )

    old_status = asset.status
    asset.status = "pending_review"
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="SUBMIT_FOR_REVIEW",
        asset_id=asset_id,
        field_name="status",
        old_value=old_status,
        new_value="pending_review",
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "message": "Asset submitted for review",
        "asset_id": asset_id,
        "status": "pending_review"
    }


# -----------------------------------
# DOWNLOAD
# redirects to cloud URL or serves local
# -----------------------------------

@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    format: str = None,
    width: int = None,
    quality: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if (
        current_user.role == "user"
        and (asset.status != "approved" and asset.status != "restricted" or not asset.is_latest)
    ):
        raise HTTPException(status_code=403, detail="Asset not available")

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

    log_usage(asset_id, "download", db, user_id=current_user.id)

    # cloud URL — redirect browser directly
    if is_cloud_url(asset.storage_path):
        target_url = asset.storage_path
        if "res.cloudinary.com" in target_url:
            transforms = []
            if format: transforms.append(f"f_{format}")
            if quality: transforms.append(f"q_{quality}")
            if width: transforms.append(f"w_{width}")
            
            if transforms:
                transform_str = ",".join(transforms)
                parts = target_url.split("/upload/")
                if len(parts) == 2:
                    target_url = f"{parts[0]}/upload/{transform_str}/{parts[1]}"
        return RedirectResponse(url=target_url)

    # local file — serve directly
    file_path = asset.storage_path
    if not os.path.exists(file_path) and os.path.exists(os.path.join(settings.STORAGE_PATH, file_path)):
        file_path = os.path.join(settings.STORAGE_PATH, file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on local storage")

    return FileResponse(
        path=file_path,
        filename=asset.original_filename
    )


# -----------------------------------
# STREAM
# serves media inline for video/audio
# -----------------------------------

@router.get("/{asset_id}/stream")
def stream_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if (
        current_user.role == "user"
        and (asset.status != "approved" and asset.status != "restricted" or not asset.is_latest)
    ):
        raise HTTPException(status_code=403, detail="Asset not available")

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

    log_usage(asset_id, "stream", db, user_id=current_user.id)

    # cloud URL — redirect browser directly
    if is_cloud_url(asset.storage_path):
        return RedirectResponse(url=asset.storage_path)

    # local file — serve directly inline
    file_path = asset.storage_path
    from app.core.config.settings import settings
    if not os.path.exists(file_path) and os.path.exists(os.path.join(settings.STORAGE_PATH, file_path)):
        file_path = os.path.join(settings.STORAGE_PATH, file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on local storage")

    return FileResponse(
        path=file_path,
        media_type=asset.mime_type
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

    if current_user.role == "user" and asset.status != "approved" and asset.status != "restricted":
        raise HTTPException(status_code=403, detail="Asset not available")

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

    preview_path = asset.preview_path or asset.thumbnail_path or asset.storage_path

    if not preview_path:
        raise HTTPException(status_code=404, detail="Preview unavailable")

    log_usage(asset_id, "preview", db, user_id=current_user.id)

    # cloud URL — redirect
    if is_cloud_url(preview_path):
        return RedirectResponse(url=preview_path)

    # local file
    if not os.path.exists(preview_path) and os.path.exists(os.path.join(settings.STORAGE_PATH, preview_path)):
        preview_path = os.path.join(settings.STORAGE_PATH, preview_path)
    if not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Preview file not found on local storage")
    
    print("-"*50)
    print("Asset Preview Path:",preview_path)
    print("Asset MIME type:", asset.mime_type)
    print("-"*50)

    import mimetypes
    guessed_type, _ = mimetypes.guess_type(preview_path)
    final_media_type = guessed_type or asset.mime_type

    return FileResponse(
        path=preview_path,
        media_type=final_media_type
    )
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

    if current_user.role == "user" and asset.status != "approved" and asset.status != "restricted":
        raise HTTPException(status_code=403, detail="Asset not available")

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

    if asset.mime_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Asset is not a PDF")

    log_usage(asset_id, "preview", db, user_id=current_user.id)

    # cloud URL — redirect so browser opens PDF natively
    if is_cloud_url(asset.storage_path):
        return RedirectResponse(url=asset.storage_path)

    file_path = asset.storage_path
    if not file_path:
        raise HTTPException(status_code=404, detail="PDF path missing")
    if not os.path.exists(file_path) and os.path.exists(os.path.join(settings.STORAGE_PATH, file_path)):
        file_path = os.path.join(settings.STORAGE_PATH, file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=file_path,
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

    if current_user.role == "user" and asset.status != "approved" and asset.status != "restricted":
        raise HTTPException(status_code=403, detail="Asset not available")

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

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

# -----------------------------------
# VERSION HISTORY
# GET /assets/{asset_id}/versions
# Returns full version tree for an asset
# -----------------------------------

@router.get("/{asset_id}/versions")
def asset_version_history(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all versions belonging to the same root asset, ordered by version number.
    """
    target = db.query(Asset).filter(Asset.id == asset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Asset not found")

    check_restricted_access(target, current_user)

    root_id = target.root_asset_id or target.id

    versions = (
        db.query(Asset)
        .filter(Asset.root_asset_id == root_id)
        .order_by(Asset.version.asc())
        .all()
    )

    result = []
    for v in versions:
        asset_name = v.original_filename
        try:
            asset_name = (
                v.asset_metadata
                .get("mandatory", {})
                .get("asset_name", v.original_filename)
            )
        except Exception:
            pass

        result.append({
            "id":                v.id,
            "version":           v.version,
            "is_latest":         v.is_latest,
            "status":            v.status,
            "original_filename": v.original_filename,
            "asset_name":        asset_name,
            "storage_path":      v.storage_path,
            "thumbnail_path":    v.thumbnail_path,
            "mime_type":         v.mime_type,
            "changelog":         v.changelog,
            "updated_by":        v.updated_by,
            "created_at":        v.created_at.isoformat() if v.created_at else None,
            "completeness_score": v.completeness_score or 0,
        })

    return {"asset_id": asset_id, "root_asset_id": root_id, "versions": result}


# -----------------------------------
# VISUAL SIMILARITY SEARCH
# GET /assets/{asset_id}/similar
# Returns visually similar images via perceptual hash
# -----------------------------------

@router.get("/{asset_id}/similar")
def find_similar_assets(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find visually similar image assets using dHash perceptual hash comparison.
    Only compares image assets. Returns assets with similarity >= VISUAL_SIMILARITY_MIN_SCORE.
    """
    target = db.query(Asset).filter(Asset.id == asset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Asset not found")

    check_restricted_access(target, current_user)

    if not target.perceptual_hash:
        raise HTTPException(
            status_code=400,
            detail="This asset does not have a perceptual hash (non-image or pre-dates this feature)."
        )

    candidates = (
        db.query(Asset)
        .filter(
            Asset.id != asset_id,
            Asset.perceptual_hash != None,
            Asset.mime_type.ilike("image/%"),
        )
        .all()
    )

    similar = []
    for candidate in candidates:
        sim = similarity_score(target.perceptual_hash, candidate.perceptual_hash)
        if sim >= VISUAL_SIMILARITY_MIN_SCORE:
            asset_name = candidate.original_filename
            try:
                asset_name = (
                    candidate.asset_metadata
                    .get("mandatory", {})
                    .get("asset_name", candidate.original_filename)
                )
            except Exception:
                pass

            similar.append({
                "asset_id":          str(candidate.id),
                "similarity_score":  sim,
                "hamming_distance":  hamming_distance(target.perceptual_hash, candidate.perceptual_hash),
                "original_filename": candidate.original_filename,
                "asset_name":        asset_name,
                "storage_path":      candidate.storage_path,
                "thumbnail_path":    candidate.thumbnail_path,
                "status":            candidate.status,
                "version":           candidate.version,
                "is_latest":         candidate.is_latest,
            })

    similar.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "asset_id":       asset_id,
        "total_similar":  len(similar),
        "similar_assets": similar,
    }


# -----------------------------------
# RETIRE ASSET
# PATCH /assets/{asset_id}/retire
# Admin only
# -----------------------------------

@router.patch("/{asset_id}/retire")
def retire_asset(
    asset_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Retire an asset: sets status = 'retired' and is_latest = False.
    A retired asset is hidden from default search but stays in DB for audit.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.status == "retired":
        raise HTTPException(status_code=400, detail="Asset is already retired")

    old_status = asset.status
    asset.status = "retired"
    asset.is_latest = False
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="RETIRE",
        asset_id=asset_id,
        field_name="status",
        old_value=old_status,
        new_value="retired",
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "message":  f"Asset {asset_id} has been retired",
        "asset_id": asset_id,
        "status":   asset.status,
    }


# -----------------------------------
# ARCHIVE ASSET
# PATCH /assets/{asset_id}/archive
# Admin only
# -----------------------------------

@router.patch("/{asset_id}/archive")
def archive_asset(
    asset_id: str,
    request: Request,
    reason: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Permanently archive an asset.
    - Sets is_archived = True
    - Records archived_at timestamp
    - Stores optional archive_reason
    - Asset is hidden from all default listing and search results
    """
    from datetime import datetime, timezone

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.is_archived:
        raise HTTPException(status_code=400, detail="Asset is already archived")

    asset.is_archived = True
    asset.archived_at = datetime.now(timezone.utc)
    asset.archive_reason = reason or ""
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="ARCHIVE",
        asset_id=asset_id,
        field_name="is_archived",
        old_value="False",
        new_value="True",
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "message":      f"Asset {asset_id} has been archived",
        "asset_id":     asset_id,
        "archived_at":  asset.archived_at.isoformat(),
        "archive_reason": asset.archive_reason,
    }


# -----------------------------------
# GET VERSION HISTORY
# -----------------------------------

# -----------------------------------
# DUPLICATE CANDIDATES
# GET /assets/duplicate-candidates
# Admin only
# -----------------------------------

@router.get("/duplicate-candidates")
def duplicate_candidates(
    threshold: int = NEAR_DUPLICATE_THRESHOLD_DISTANCE,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Scan all image assets and return groups of near-duplicate candidates.
    Uses perceptual hash Hamming distance <= threshold (default 10).
    """
    image_assets = (
        db.query(Asset)
        .filter(
            Asset.perceptual_hash != None,
            Asset.mime_type.ilike("image/%"),
        )
        .all()
    )

    visited = set()
    groups = []

    for i, a in enumerate(image_assets):
        if a.id in visited:
            continue
        group = [a]
        for j in range(i + 1, len(image_assets)):
            b = image_assets[j]
            if b.id in visited:
                continue
            dist = hamming_distance(a.perceptual_hash, b.perceptual_hash)
            if dist <= threshold:
                group.append(b)
                visited.add(b.id)

        if len(group) > 1:
            visited.add(a.id)

            def _summary(asset):
                asset_name = asset.original_filename
                try:
                    asset_name = (
                        asset.asset_metadata
                        .get("mandatory", {})
                        .get("asset_name", asset.original_filename)
                    )
                except Exception:
                    pass
                return {
                    "asset_id":          str(asset.id),
                    "asset_name":        asset_name,
                    "original_filename": asset.original_filename,
                    "thumbnail_path":    asset.thumbnail_path,
                    "status":            asset.status,
                    "version":           asset.version,
                    "perceptual_hash":   asset.perceptual_hash,
                }

            groups.append({
                "group_size": len(group),
                "assets":     [_summary(x) for x in group],
            })

    return {
        "total_groups":      len(groups),
        "hamming_threshold": threshold,
        "duplicate_groups":  groups,
    }

# -----------------------------------
# DUPLICATE MERGE / REPLACE
# POST / assets/resolve-duplicate
# Admin only
# -----------------------------------

@router.post(
        "/resolve-duplicate",
        response_model=DuplicateResolveResponse
)

def resolve_duplicate_asset(
    request:DuplicateResolveRequest,
    req: Request,
    db:Session=Depends(get_db),
    current_user:User=Depends(require_admin)
):
    """
    Resolve a duplicate asset by merging its metadata into
    a canonical asset and then retiring or deleting the
    duplicate asset.

    Workflow
    --------
    1. Validate assets
    2. Merge metadata (optional)
    3. Retire OR Delete duplicate
    4. Return workflow summary

    NOTE:
    ChromaDB synchronization is added in Phase 2.4.4.
    """

    DuplicateMergeService.resolve(
        db=db,
        canonical_asset_id=request.canonical_asset_id,
        duplicate_asset_id=request.duplicate_asset_id,
        action=request.action,
        merge_metadata=request.merge_metadata
    )

    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="RESOLVE_DUPLICATE",
        asset_id=request.canonical_asset_id,
        field_name="duplicate_asset_id",
        old_value=request.duplicate_asset_id,
        new_value=f"Action: {request.action}, Merged: {request.merge_metadata}",
        ip_address=req.client.host if req.client else None
    )
    db.commit()

    return DuplicateResolveResponse(
        success=True,
        message=(
            f"Duplicate asset successfully "
            f"{'retired' if request.action == 'retire' else 'deleted'}."
        ),
        canonical_asset_id=request.canonical_asset_id,
        duplicate_asset_id=request.duplicate_asset_id,
        action=request.action,
        metadata_merged=request.merge_metadata,
    )

# -----------------------------------
# BULK EDIT
# -----------------------------------
@router.put("/bulk-edit")
def bulk_edit_assets(
    payload: AssetBulkEditRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    assets = db.query(Asset).filter(Asset.id.in_(payload.asset_ids)).all()
    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for given IDs")

    updated_count = 0
    for asset in assets:
        # Merge metadata updates
        if payload.metadata_updates:
            current_metadata = asset.asset_metadata or {}
            
            # Simple shallow merge by key sections (mandatory, business, etc.)
            for section, updates in payload.metadata_updates.items():
                if section not in current_metadata:
                    current_metadata[section] = {}
                if isinstance(updates, dict):
                    current_metadata[section].update(updates)
                else:
                    current_metadata[section] = updates
                    
            asset.asset_metadata = current_metadata
            
            # Recalculate completeness score
            from app.utils.completeness import calculate_completeness
            asset.completeness_score = calculate_completeness(current_metadata)

        # Apply scalar updates
        if payload.status is not None:
            asset.status = payload.status
        if payload.website_safe is not None:
            asset.website_safe = payload.website_safe
        if payload.public_use_approved is not None:
            asset.public_use_approved = payload.public_use_approved
        if payload.brand_aligned is not None:
            asset.brand_aligned = payload.brand_aligned
        if payload.alt_text is not None:
            asset.alt_text = payload.alt_text
        if payload.geographic_restrictions is not None:
            asset.geographic_restrictions = payload.geographic_restrictions
        if payload.platform_restrictions is not None:
            asset.platform_restrictions = payload.platform_restrictions
        if payload.source_ownership is not None:
            asset.source_ownership = payload.source_ownership
        if payload.model_release_status is not None:
            asset.model_release_status = payload.model_release_status

        asset.updated_by = current_user.email if hasattr(current_user, "email") else str(current_user.id)
        
        # Log audit
        log_audit_event(
            db=db,
            user_id=current_user.id,
            action="BULK_EDIT",
            asset_id=asset.id,
            new_value="Bulk metadata update applied",
            ip_address=request.client.host if request.client else None
        )
        updated_count += 1
        
    db.commit()
    return {"message": f"Successfully updated {updated_count} assets."}

# -----------------------------------
# GET SINGLE ASSET
# IMPORTANT: This catch-all route MUST be last
# so it does not intercept named routes like
# /duplicate-candidates
# -----------------------------------

@router.get("/{asset_id}")
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Access control for restricted view roles
    RESTRICTED_VIEW_ROLES = ["user", "sales_user", "external_partner"]
    if current_user.role in RESTRICTED_VIEW_ROLES:
        if asset.status != "approved" and asset.status != "restricted": # Allow restricted assets to be checked by check_restricted_access
            if asset.status != "approved" or asset.is_archived:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this asset"
                )

    # Enforce Phase 4.1 restricted access control
    check_restricted_access(asset, current_user)

    # Domain-scoped access control
    if current_user.allowed_domains:
        try:
            asset_domain = asset.asset_metadata.get("business", {}).get("domain")
            if asset_domain not in current_user.allowed_domains:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access assets in this domain"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to verify asset domain scope"
            )

    # return asset

    # --------------------------------------------------------------
    # Feature 3.3 - Automatic Expiry Check
    # --------------------------------------------------------------

    ExpiryService.auto_restrict_if_expired(asset=asset, db=db)

    db.refresh(asset)

    expiry=ExpiryService.build_expiry_status(asset)

    # --------------------------------------------------------------
    # Return enriched asset response
    # --------------------------------------------------------------

    # Fetch derivatives
    derivatives = db.query(Asset).filter(
        Asset.parent_id == asset.id,
        Asset.relationship_type == "derivative"
    ).all()
    
    # Fetch master if this is a derivative
    master_asset = None
    if asset.relationship_type == "derivative" and asset.parent_id:
        master_asset = db.query(Asset).filter(Asset.id == asset.parent_id).first()

    # Fetch renditions
    from app.models.asset.asset_rendition_model import AssetRendition
    asset_renditions = db.query(AssetRendition).filter(AssetRendition.asset_id == asset.id).all()

    return {
        **asset.__dict__,
        "metadata": asset.asset_metadata,
        "derivatives": [
            {"id": d.id, "original_filename": d.original_filename, "version": d.version, "created_at": d.created_at} 
            for d in derivatives
        ],
        "master_asset": {"id": master_asset.id, "original_filename": master_asset.original_filename} if master_asset else None,
        "renditions": [r.__dict__ for r in asset_renditions],
        **expiry,
    }

# -----------------------------------
# ASSET PLACEMENTS
# -----------------------------------

@router.post("/{asset_id}/placements", response_model=AssetPlacementResponse)
def add_placement(
    asset_id: str,
    payload: AssetPlacementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    check_restricted_access(asset, current_user)
    
    placement = AssetPlacement(
        asset_id=asset_id,
        platform=payload.platform,
        placement_url_or_id=payload.placement_url_or_id,
        added_by=current_user.email if hasattr(current_user, "email") else str(current_user.id)
    )
    db.add(placement)
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="ADD_PLACEMENT",
        asset_id=asset_id,
        field_name="platform",
        new_value=f"{payload.platform}: {payload.placement_url_or_id}",
        ip_address=request.client.host if request.client else None
    )
    db.commit()
    db.refresh(placement)
    return placement

@router.get("/{asset_id}/placements")
def list_placements(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    check_restricted_access(asset, current_user)
    
    placements = db.query(AssetPlacement).filter(AssetPlacement.asset_id == asset_id).all()
    return placements
