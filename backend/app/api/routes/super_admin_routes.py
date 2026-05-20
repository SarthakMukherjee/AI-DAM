from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import (
    require_super_admin,
    require_admin_or_reviewer
)

from app.models.user.user_model import User
from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage
from app.models.user.notification_model import Notification

from app.schemas.user.schemas import (
    UserResponse,
    UpdateRoleRequest,
    NotificationResponse,
    TopAssetsResponse,
    AssetUsageResponse
)


router = APIRouter(
    prefix="/super-admin",
    tags=["Super Admin"]
)


# =====================================================
# USER MANAGEMENT — super_admin only
# =====================================================

# -----------------------------------
# LIST ALL USERS
# -----------------------------------

@router.get(
    "/users",
    response_model=list[UserResponse]
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin)
):

    return db.query(User).all()


# -----------------------------------
# PROMOTE / DEMOTE USER
# super_admin can assign any role
# cannot change their own role
# -----------------------------------

@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse
)
def update_user_role(
    user_id: str,
    body: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):

    allowed_roles = [
        "super_admin",
        "admin",
        "reviewer",
        "user"
    ]

    if body.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {allowed_roles}"
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    old_role = user.role

    user.role = body.role

    db.commit()
    db.refresh(user)

    return user


# -----------------------------------
# DEACTIVATE USER
# soft delete, cannot deactivate self
# -----------------------------------

@router.patch(
    "/users/{user_id}/deactivate"
)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False

    db.commit()

    return {
        "message": f"User {user.email} deactivated"
    }


# -----------------------------------
# REACTIVATE USER
# -----------------------------------

@router.patch(
    "/users/{user_id}/reactivate"
)
def reactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin)
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True

    db.commit()

    return {
        "message": f"User {user.email} reactivated"
    }


# =====================================================
# ASSET MANAGEMENT — super_admin only
# =====================================================

# -----------------------------------
# LIST ALL ASSETS (any status)
# -----------------------------------

@router.get("/assets")
def list_all_assets(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin)
):

    return db.query(Asset).all()


# -----------------------------------
# DELETE ASSET
# hard delete from DB and disk
# -----------------------------------

@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin)
):

    import os

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

    for path in [
        asset.storage_path,
        asset.thumbnail_path,
        asset.preview_path
    ]:
        if path and os.path.exists(path):
            os.remove(path)

    db.delete(asset)
    db.commit()

    return {"message": "Asset deleted"}


# =====================================================
# NOTIFICATIONS — super_admin
# =====================================================

@router.get(
    "/notifications",
    response_model=list[NotificationResponse]
)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
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
    current_user: User = Depends(require_super_admin)
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
    current_user: User = Depends(require_super_admin)
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
# ANALYTICS — super_admin + admin + reviewer
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
            func.sum(AssetUsage.usage_count).label(
                "total_usage"
            )
        )
        .join(
            AssetUsage,
            Asset.id == AssetUsage.asset_id
        )
        .group_by(Asset.id)
        .order_by(
            func.sum(AssetUsage.usage_count).desc()
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
        .filter(AssetUsage.asset_id == asset_id)
        .scalar()
    ) or 0

    by_action = (
        db.query(
            AssetUsage.action,
            func.sum(AssetUsage.usage_count).label("count")
        )
        .filter(AssetUsage.asset_id == asset_id)
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