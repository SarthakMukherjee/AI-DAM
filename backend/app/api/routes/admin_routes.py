from fastapi import APIRouter, Depends, HTTPException, status

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

from app.schemas.user.schemas import (
    NotificationResponse,
    TopAssetsResponse,
    AssetUsageResponse
)

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
    # DELETE FILES / FOLDERS
    # skip cloud URLs — nothing to delete locally
    # ==========================================

    paths_to_delete = [
        asset.storage_path,
        asset.thumbnail_path,
        asset.preview_path
    ]

    for path in paths_to_delete:

        if not path:
            continue

        if path.startswith("http"):
            continue

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
            func.sum(
                AssetUsage.usage_count
            ).label("total_usage")
        )
        .join(
            AssetUsage,
            Asset.id == AssetUsage.asset_id
        )
        .group_by(Asset.id)
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
                total_usage=row.total_usage or 0
            )
        )

    return TopAssetsResponse(top_assets=top_assets)


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