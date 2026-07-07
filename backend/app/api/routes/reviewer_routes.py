from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import require_reviewer
from app.models.user.user_model import User
from app.models.asset.asset_model import Asset
from app.models.user.notification_model import Notification
from app.schemas.user.schemas import ReviewRequest, PublishRequest, RestrictRequest, ApproveRequest

router = APIRouter(prefix="/reviewer", tags=["Reviewer"])

def check_reviewer_scope(asset: Asset, user: User) -> None:
    """Enforces that scoped reviewers can only review assets in their allowed_domains (Phase 4.3)."""
    if user.allowed_domains:
        try:
            asset_domain = (asset.asset_metadata or {}).get("business", {}).get("domain")
            if asset_domain not in user.allowed_domains:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You are not authorized to review assets in this domain"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Failed to verify reviewer domain scope"
            )


@router.get("/queue")
def review_queue(db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    query = db.query(Asset).filter(Asset.status.in_(["draft", "pending_review"]))
    if current_user.allowed_domains:
        domain_filter = Asset.asset_metadata["business"]["domain"].as_string().in_(current_user.allowed_domains)
        query = query.filter(domain_filter)
    return query.order_by(Asset.created_at.asc()).all()

@router.post("/assets/{asset_id}/approve")
def approve_asset(asset_id: str, body: ApproveRequest = None, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    check_reviewer_scope(asset, current_user)
    if asset.status not in ["draft", "pending_review"]: raise HTTPException(status_code=400, detail=f"Asset is already {asset.status}")
    
    asset.status = "approved"
    
    if body:
        if body.website_safe is not None:
            asset.website_safe = body.website_safe
        if body.public_use_approved is not None:
            asset.public_use_approved = body.public_use_approved
        if body.brand_aligned is not None:
            asset.brand_aligned = body.brand_aligned
            
    db.commit()
    return {"message": "Asset approved", "asset_id": asset_id}

@router.post("/assets/{asset_id}/reject")
def reject_asset(asset_id: str, body: ReviewRequest, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    check_reviewer_scope(asset, current_user)
    if asset.status not in ["draft", "pending_review", "approved"]: raise HTTPException(status_code=400, detail=f"Cannot reject: {asset.status}")
    asset.status = "rejected"
    db.commit()
    recipients = db.query(User).filter(User.role.in_(["admin", "super_admin"]), User.is_active == True).all()
    try: asset_name = asset.asset_metadata.get("mandatory", {}).get("asset_name", asset.original_filename)
    except: asset_name = asset.original_filename
    msg = f"Asset rejected: {asset_name}."
    if body.rejection_category: msg += f" Category: {body.rejection_category}."
    for r in recipients: db.add(Notification(user_id=r.id, asset_id=asset_id, message=msg, reason=body.reason))
    db.commit()
    return {"message": "Asset rejected", "asset_id": asset_id, "rejection_category": body.rejection_category, "reason": body.reason}

@router.post("/assets/{asset_id}/publish")
def publish_asset(asset_id: str, body: PublishRequest, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    check_reviewer_scope(asset, current_user)
    if asset.status != "approved": raise HTTPException(status_code=400, detail=f"Only approved assets can be published. Current: {asset.status}")
    asset.status = "published"
    if body.publish_note or body.published_channels:
        meta = dict(asset.asset_metadata or {})
        meta.setdefault("governance", {})
        if body.publish_note: meta["governance"]["publish_note"] = body.publish_note
        if body.published_channels: meta["governance"]["published_channels"] = body.published_channels
        asset.asset_metadata = meta
    db.commit()
    return {"message": "Asset published", "asset_id": asset_id, "status": "published"}

@router.post("/assets/{asset_id}/restrict")
def restrict_asset(asset_id: str, body: RestrictRequest, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    check_reviewer_scope(asset, current_user)
    asset.status = "restricted"
    meta = dict(asset.asset_metadata or {})
    meta.setdefault("governance", {})
    meta["governance"]["restriction_reason"] = body.reason or "Restricted by reviewer"
    meta["governance"]["restricted_to_roles"] = body.restricted_to_roles or ["admin", "reviewer", "super_admin"]
    asset.asset_metadata = meta
    db.commit()
    return {"message": "Asset restricted", "asset_id": asset_id, "status": "restricted", "reason": body.reason}

@router.post("/assets/{asset_id}/unrestrict")
def unrestrict_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    check_reviewer_scope(asset, current_user)
    if asset.status != "restricted": raise HTTPException(status_code=400, detail="Asset is not restricted")
    asset.status = "approved"
    db.commit()
    return {"message": "Asset unrestricted. Status set to approved.", "asset_id": asset_id}
