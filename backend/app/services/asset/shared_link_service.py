import uuid
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.asset.shared_link_model import SharedLink
from app.models.asset.asset_model import Asset
from app.schemas.shared_link_schema import SharedLinkCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SharedLinkService:
    @staticmethod
    def create_link(db: Session, req: SharedLinkCreate, user_id: str) -> SharedLink:
        # Check if asset exists and is approved/published
        asset = db.query(Asset).filter(Asset.id == req.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        if asset.status not in ("approved", "published"):
            raise HTTPException(status_code=400, detail="Can only share approved or published assets")

        # Generate a secure token
        token = secrets.token_urlsafe(32)
        
        expires_at = None
        if req.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)
            
        password_hash = None
        if req.password:
            password_hash = pwd_context.hash(req.password)
            
        link = SharedLink(
            token=token,
            asset_id=req.asset_id,
            created_by=user_id,
            expires_at=expires_at,
            password_hash=password_hash
        )
        
        db.add(link)
        db.commit()
        db.refresh(link)
        
        return link

    @staticmethod
    def get_link_by_token(db: Session, token: str) -> SharedLink:
        link = db.query(SharedLink).filter(SharedLink.token == token).first()
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
            
        if link.expires_at and link.expires_at.replace(tzinfo=None) < datetime.utcnow():
            raise HTTPException(status_code=410, detail="This shared link has expired")
            
        return link
        
    @staticmethod
    def verify_password(link: SharedLink, password: str | None) -> bool:
        if not link.password_hash:
            return True
        if not password:
            return False
        return pwd_context.verify(password, link.password_hash)
