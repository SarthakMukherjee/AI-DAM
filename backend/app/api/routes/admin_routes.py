from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

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
from app.models.analytics.search_log_model import SearchLog

from app.schemas.user.schemas import (
    NotificationResponse,
    TopAssetsResponse,
    AssetUsageResponse
)
from app.schemas.audit_schema import PaginatedAuditLogs
from app.schemas.analytics_schema import (
    UnusedAssetsResponse,
    MissingMetadataResponse,
    ApprovalTimeResponse,
    SearchGapResponse
)

from app.services.storage.cloud_service import CloudService
from app.services.storage.expiry_service import ExpiryService

from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import shutil
import io
import csv


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


@router.get("/analytics/missing-metadata", response_model=MissingMetadataResponse)
def get_missing_metadata(
    threshold: int = Query(default=60, ge=0, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Get active, latest-version assets whose metadata completeness score falls below the threshold.
    """
    assets = (
        db.query(Asset)
        .filter(
            Asset.is_latest == True,
            Asset.is_archived == False,
            Asset.completeness_score < threshold
        )
        .order_by(Asset.completeness_score.asc(), Asset.created_at.desc())
        .all()
    )

    results = []
    for asset in assets:
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
            "alt_text": asset.alt_text,
            "completeness_score": asset.completeness_score,
        })

    return {
        "total": len(results),
        "threshold": threshold,
        "items": results
    }

@router.get("/analytics/approval-times", response_model=ApprovalTimeResponse)
def get_approval_times(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Measure workflow bottleneck metrics (average time spent in pending_review before being approved or rejected).
    """
    # We join AuditLog with Asset. We find AuditLogs where action in ('APPROVE', 'REJECT').
    # We compute the difference between AuditLog.timestamp and Asset.created_at (as a proxy for pending review duration).
    
    logs = (
        db.query(AuditLog, Asset)
        .join(Asset, AuditLog.asset_id == Asset.id)
        .filter(AuditLog.action.in_(["APPROVE", "REJECT"]))
        .all()
    )
    
    if not logs:
        return {
            "global_metrics": {
                "average_hours": 0.0,
                "total_approved": 0,
                "total_rejected": 0
            },
            "by_domain": {}
        }
        
    total_seconds = 0
    total_approved = 0
    total_rejected = 0
    domain_seconds = {}
    domain_counts = {}
    
    for log, asset in logs:
        if log.action == "APPROVE":
            total_approved += 1
        elif log.action == "REJECT":
            total_rejected += 1
            
        # compute duration
        if log.timestamp and asset.created_at:
            delta = log.timestamp - asset.created_at
            seconds = delta.total_seconds()
            if seconds < 0:
                seconds = 0
            
            total_seconds += seconds
            
            # extract domain
            domain = "Unknown"
            if asset.asset_metadata and "business" in asset.asset_metadata:
                domain = asset.asset_metadata["business"].get("domain") or "Unknown"
                
            if domain not in domain_seconds:
                domain_seconds[domain] = 0
                domain_counts[domain] = 0
            domain_seconds[domain] += seconds
            domain_counts[domain] += 1
            
    total_count = total_approved + total_rejected
    avg_hours = (total_seconds / total_count) / 3600.0 if total_count > 0 else 0.0
    
    by_domain = {}
    for dom in domain_seconds:
        by_domain[dom] = (domain_seconds[dom] / domain_counts[dom]) / 3600.0
        
    return {
        "global_metrics": {
            "average_hours": avg_hours,
            "total_approved": total_approved,
            "total_rejected": total_rejected
        },
        "by_domain": by_domain
    }

@router.get("/analytics/search-gaps", response_model=SearchGapResponse)
def get_search_gaps(
    min_results: int = Query(default=2, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Return top search queries where average results_count < min_results.
    """
    gaps = (
        db.query(
            SearchLog.query,
            SearchLog.search_type,
            func.count(SearchLog.id).label("count"),
            func.avg(SearchLog.results_count).label("avg_results")
        )
        .group_by(SearchLog.query, SearchLog.search_type)
        .having(func.avg(SearchLog.results_count) < min_results)
        .order_by(func.count(SearchLog.id).desc())
        .limit(50)
        .all()
    )
    
    items = []
    for row in gaps:
        items.append({
            "query": row.query,
            "search_type": row.search_type,
            "count": row.count,
            "avg_results": float(row.avg_results)
        })
        
    return {"items": items}

@router.get("/analytics/export")
def export_analytics(
    report_type: str = Query(..., description="unused | missing_meta | audit | most_used | approval_times | search_gaps"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Export analytics data as CSV.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == "unused":
        writer.writerow(["Asset ID", "Original Filename", "File Size", "Created At", "Status"])
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        used_ids = db.query(AssetUsage.asset_id).filter(AssetUsage.action.in_(["download", "preview"])).distinct()
        assets = db.query(Asset).filter(Asset.created_at <= cutoff, Asset.is_archived == False, Asset.is_latest == True, ~Asset.id.in_(used_ids)).all()
        for a in assets:
            writer.writerow([a.id, a.original_filename, a.file_size, a.created_at, a.status])
            
    elif report_type == "missing_meta":
        writer.writerow(["Asset ID", "Original Filename", "Completeness Score", "Created At", "Status"])
        assets = db.query(Asset).filter(Asset.is_latest == True, Asset.is_archived == False, Asset.completeness_score < 60).all()
        for a in assets:
            writer.writerow([a.id, a.original_filename, getattr(a, 'completeness_score', 0), a.created_at, a.status])
            
    elif report_type == "audit":
        writer.writerow(["Log ID", "User ID", "Asset ID", "Action", "Field", "Old Value", "New Value", "Timestamp"])
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1000).all()
        for log in logs:
            writer.writerow([log.id, log.user_id, log.asset_id, log.action, log.field_name, log.old_value, log.new_value, log.timestamp])
            
    elif report_type == "most_used":
        writer.writerow(["Asset ID", "Original Filename", "Total Usage"])
        results = (
            db.query(Asset.id, Asset.original_filename, func.sum(AssetUsage.usage_count).label("total_usage"))
            .join(AssetUsage, Asset.id == AssetUsage.asset_id)
            .group_by(Asset.id, Asset.original_filename)
            .order_by(func.sum(AssetUsage.usage_count).desc())
            .limit(100).all()
        )
        for r in results:
            writer.writerow([r.id, r.original_filename, r.total_usage])
            
    elif report_type == "approval_times":
        writer.writerow(["Asset ID", "Action", "User ID", "Duration (Hours)", "Timestamp"])
        logs = (
            db.query(AuditLog, Asset)
            .join(Asset, AuditLog.asset_id == Asset.id)
            .filter(AuditLog.action.in_(["APPROVE", "REJECT"]))
            .all()
        )
        for log, asset in logs:
            delta = log.timestamp - asset.created_at
            hours = delta.total_seconds() / 3600.0 if delta.total_seconds() > 0 else 0
            writer.writerow([asset.id, log.action, log.user_id, f"{hours:.2f}", log.timestamp])
            
    elif report_type == "search_gaps":
        writer.writerow(["Query", "Search Type", "Search Count", "Average Results"])
        gaps = (
            db.query(SearchLog.query, SearchLog.search_type, func.count(SearchLog.id).label("count"), func.avg(SearchLog.results_count).label("avg_results"))
            .group_by(SearchLog.query, SearchLog.search_type)
            .having(func.avg(SearchLog.results_count) < 2)
            .order_by(func.count(SearchLog.id).desc())
            .limit(100).all()
        )
        for r in gaps:
            writer.writerow([r.query, r.search_type, r.count, f"{r.avg_results:.2f}"])
            
    else:
        raise HTTPException(status_code=400, detail="Invalid report_type")
        
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{report_type}.csv"}
    )
