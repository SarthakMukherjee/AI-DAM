from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import (
    require_admin,
    require_admin_or_reviewer
)

from app.models.user.user_model import User
from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage
from app.models.user.notification_model import Notification
from app.models.audit.audit_log_model import AuditLog

from app.schemas.user.schemas import (
    NotificationResponse,
    TopAssetsResponse,
    AssetUsageResponse
)
from app.schemas.audit_schema import PaginatedAuditLogs
from app.schemas.analytics_schema import UnusedAssetsResponse

from app.services.storage.cloud_service import CloudService
from app.services.storage.expiry_service import ExpiryService

from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import shutil


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# =====================================================
# ASSET MANAGEMENT
# super_admin + admin
# =====================================================

# -----------------------------------
# LIST ALL ASSETS (any status)
# -----------------------------------

@router.get("/assets")
def list_all_assets(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return db.query(Asset).all()


# -----------------------------------
# DELETE ASSET
# super_admin + admin
# hard deletes file + previews + DB
# -----------------------------------

@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # ==========================================
    # DELETE RELATED RECORDS FIRST
    # order matters — must delete child records
    # before deleting the parent asset
    # ==========================================

    db.query(AssetUsage).filter(
        AssetUsage.asset_id == asset_id
    ).delete()

    db.query(Notification).filter(
        Notification.asset_id == asset_id
    ).delete()

    # ==========================================
    # DELETE FILES
    # cloud URLs → delete from Cloudinary
    # local paths → delete from disk
    # ==========================================

    paths_to_delete = [
        asset.storage_path,
        asset.thumbnail_path,
        asset.preview_path
    ]

    for path in paths_to_delete:

        if not path:
            continue

        # cloud URL — delete from Cloudinary
        if path.startswith("http"):
            try:
                # extract public_id from Cloudinary URL
                # e.g. https://res.cloudinary.com/xxx/image/upload/v123/ai-dam/originals/file.png
                # public_id = ai-dam/originals/file
                parts = path.split("/upload/")
                if len(parts) == 2:
                    public_id_with_version = parts[1]
                    # strip version prefix (v1234567/)
                    public_id_parts = public_id_with_version.split("/", 1)
                    if (
                        public_id_parts[0].startswith("v")
                        and public_id_parts[0][1:].isdigit()
                    ):
                        public_id = public_id_parts[1]
                    else:
                        public_id = public_id_with_version
                    # strip file extension
                    public_id = public_id.rsplit(".", 1)[0]
                    CloudService.delete(
                        public_id=public_id,
                        resource_type="image"
                    )
                    print(f"[CLOUDINARY] Deleted: {public_id}")
            except Exception as e:
                print(f"[CLOUDINARY] Failed to delete {path}: {e}")
            continue

        # local file — delete from disk
        if os.path.exists(path):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f"Failed deleting path: {path} — {e}")

    # ==========================================
    # DELETE ASSET RECORD
    # ==========================================

    db.delete(asset)
    db.commit()

    return {"message": "Asset deleted successfully"}


# =====================================================
# NOTIFICATIONS
# admin receives rejection alerts
# =====================================================

@router.get(
    "/notifications",
    response_model=list[NotificationResponse]
)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch(
    "/notifications/{notification_id}/read"
)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@router.patch("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .update({"is_read": True})
    )

    db.commit()

    return {"message": "All notifications marked as read"}


# =====================================================
# ANALYTICS
# super_admin + admin + reviewer
# =====================================================

@router.get(
    "/analytics/most-used",
    response_model=TopAssetsResponse
)
def most_used_assets(
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_reviewer)
):

    results = (
        db.query(
            Asset.id,
            Asset.original_filename,
            Asset.asset_metadata,
            Asset.thumbnail_path,
            Asset.preview_path,
            func.sum(
                AssetUsage.usage_count
            ).label("total_usage")
        )
        .join(
            AssetUsage,
            Asset.id == AssetUsage.asset_id
        )
        .group_by(
            Asset.id,
            Asset.original_filename,
            Asset.asset_metadata,
            Asset.thumbnail_path,
            Asset.preview_path
        )
        .order_by(
            func.sum(
                AssetUsage.usage_count
            ).desc()
        )
        .limit(limit)
        .all()
    )

    top_assets = []

    for row in results:

        asset_name = ""

        try:
            asset_name = (
                row.asset_metadata
                .get("mandatory", {})
                .get("asset_name", "")
            )
        except Exception:
            pass

        top_assets.append(
            AssetUsageResponse(
                asset_id=row.id,
                original_filename=row.original_filename,
                asset_name=asset_name,
                thumbnail_path=row.thumbnail_path,
                preview_path=row.preview_path,
                total_usage=row.total_usage or 0
            )
        )

    return TopAssetsResponse(
        top_assets=top_assets
    )

@router.get("/analytics/asset/{asset_id}")
def asset_usage(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_reviewer)
):

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    total = (
        db.query(
            func.sum(AssetUsage.usage_count)
        )
        .filter(
            AssetUsage.asset_id == asset_id
        )
        .scalar()
    ) or 0

    by_action = (
        db.query(
            AssetUsage.action,
            func.sum(
                AssetUsage.usage_count
            ).label("count")
        )
        .filter(
            AssetUsage.asset_id == asset_id
        )
        .group_by(AssetUsage.action)
        .all()
    )

    return {
        "asset_id": asset_id,
        "original_filename": asset.original_filename,
        "total_usage": total,
        "by_action": {
            row.action: row.count
            for row in by_action
        }
    }


# =====================================================
# EXPIRY MONITORING
# admin + super_admin
# =====================================================

@router.get("/assets/expiring")
def list_expiring_assets(
    days_threshold: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Return all assets that are expired or expiring within `days_threshold` days.
    Each result includes computed `expired`, `expiring_soon`, and `days_until_expiry` flags.
    """
    expiring = ExpiryService.get_expiring_assets(db, threshold_days=days_threshold)

    results = []
    for item in expiring:
        asset = item["asset"]
        meta = asset.asset_metadata or {}
        mandatory = meta.get("mandatory", {})
        business = meta.get("business", {})
        results.append({
            "asset_id": asset.id,
            "original_filename": asset.original_filename,
            "asset_name": mandatory.get("asset_name", asset.original_filename),
            "status": asset.status,
            "domain": business.get("domain", ""),
            "expiry_date": business.get("expiry_date", ""),
            "thumbnail_path": asset.thumbnail_path,
            "expired": item.get("expired", False),
            "expiring_soon": item.get("expiring_soon", False),
            "days_until_expiry": item.get("days_until_theory"),
        })

    return {"expiring_assets": results, "count": len(results)}


@router.post("/assets/{asset_id}/check-expiry")
def check_asset_expiry(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Manually trigger expiry check for a specific asset.
    If expired, auto-restricts asset and creates admin notifications.
    Returns current expiry status.
    """
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    status_changed = ExpiryService.auto_restrict_if_expired(asset, db)
    expiry_status = ExpiryService.build_expiry_status(asset)

    return {
        "asset_id": asset_id,
        "status_changed": status_changed,
        "current_status": asset.status,
        **expiry_status,
        "message": (
            "Asset has been automatically restricted due to expiry."
            if status_changed
            else "No status change — asset is not expired or already restricted."
        )
    }


# =====================================================
# AUDIT TRAILS & ANALYTICS REPORTS (Phase 5)
# admin + super_admin
# =====================================================

@router.get("/audit-logs", response_model=PaginatedAuditLogs)
def get_audit_logs(
    asset_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Get paginated and queryable audit logs (Admin only).
    """
    query = db.query(AuditLog)
    if asset_id:
        query = query.filter(AuditLog.asset_id == asset_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    if from_date:
        try:
            if len(from_date) == 10:
                dt_from = datetime.strptime(from_date, "%Y-%m-%d")
            else:
                dt_from = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            # convert offset-naive to aware if necessary (based on DB schema)
            query = query.filter(AuditLog.timestamp >= dt_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD or ISO 8601.")
            
    if to_date:
        try:
            if len(to_date) == 10:
                dt_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                dt_to = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query = query.filter(AuditLog.timestamp <= dt_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD or ISO 8601.")

    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 1
    offset = (page - 1) * limit
    items = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "items": items
    }


@router.get("/analytics/unused-assets", response_model=UnusedAssetsResponse)
def get_unused_assets(
    days: int = Query(default=90, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Get assets that are older than `days` and have zero downloads or previews.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Subquery of assets that have been used (downloaded or previewed)
    used_asset_ids_subquery = (
        db.query(AssetUsage.asset_id)
        .filter(AssetUsage.action.in_(["download", "preview"]))
        .distinct()
    )
    
    unused_assets = (
        db.query(Asset)
        .filter(
            Asset.created_at <= cutoff,
            Asset.is_archived == False,
            Asset.is_latest == True,
            ~Asset.id.in_(used_asset_ids_subquery)
        )
        .all()
    )

    results = []
    for asset in unused_assets:
        expiry = ExpiryService.build_expiry_status(asset)
        results.append({
            "id": asset.id,
            "original_filename": asset.original_filename,
            "stored_filename": asset.stored_filename,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
            "metadata": asset.asset_metadata,
            "status": asset.status,
            "version": asset.version,
            "parent_id": asset.parent_id,
            "is_latest": asset.is_latest,
            "is_archived": asset.is_archived,
            "thumbnail_path": asset.thumbnail_path,
            "preview_path": asset.preview_path,
            "expired": expiry.get("expired", False),
            "expiring_soon": expiry.get("expiring_soon", False),
            "days_until_expiry": expiry.get("days_until_expiry"),
            "created_at": asset.created_at,
            "website_safe": asset.website_safe,
            "public_use_approved": asset.public_use_approved,
            "brand_aligned": asset.brand_aligned,
            "alt_text": asset.alt_text
        })

    return {
        "total": len(results),
        "days_threshold": days,
        "items": results
    }
