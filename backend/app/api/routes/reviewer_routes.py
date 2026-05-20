from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import (
    require_reviewer
)

from app.models.user.user_model import User
from app.models.asset.asset_model import Asset
from app.models.user.notification_model import Notification

from app.schemas.user.schemas import ReviewRequest


router = APIRouter(
    prefix="/reviewer",
    tags=["Reviewer"]
)


# -----------------------------------
# REVIEW QUEUE
# all draft assets pending review
# super_admin + reviewer
# -----------------------------------

@router.get("/queue")
def review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer)
):

    return (
        db.query(Asset)
        .filter(Asset.status == "draft")
        .order_by(Asset.created_at.asc())
        .all()
    )


# -----------------------------------
# APPROVE ASSET
# super_admin + reviewer
# sets status to "approved"
# -----------------------------------

@router.post("/assets/{asset_id}/approve")
def approve_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer)
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

    if asset.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset is already {asset.status}"
        )

    asset.status = "approved"

    db.commit()

    return {
        "message": "Asset approved",
        "asset_id": asset_id
    }


# -----------------------------------
# REJECT ASSET
# super_admin + reviewer
# sets status to "rejected"
# notifies all admins + super_admin
# reason is optional
# -----------------------------------

@router.post("/assets/{asset_id}/reject")
def reject_asset(
    asset_id: str,
    body: ReviewRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_reviewer)
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

    if asset.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset is already {asset.status}"
        )

    asset.status = "rejected"

    db.commit()

    # -----------------------------------
    # NOTIFY ALL ADMINS + SUPER ADMINS
    # -----------------------------------

    recipients = (
        db.query(User)
        .filter(
            User.role.in_(["admin", "super_admin"]),
            User.is_active == True
        )
        .all()
    )

    asset_name = ""

    try:
        asset_name = (
            asset.asset_metadata
            .get("mandatory", {})
            .get("asset_name", asset.original_filename)
        )
    except Exception:
        asset_name = asset.original_filename

    for recipient in recipients:

        notification = Notification(
            user_id=recipient.id,
            asset_id=asset_id,
            message=(
                f"Asset '{asset_name}' was rejected by reviewer."
            ),
            reason=body.reason
        )

        db.add(notification)

    db.commit()

    return {
        "message": "Asset rejected and admins notified",
        "asset_id": asset_id,
        "reason": body.reason
    }