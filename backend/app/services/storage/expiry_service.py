from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset
from app.models.user.notification_model import Notification
from app.models.user.user_model import User

class ExpiryService:
    """
    Handles expiry-date related operations for assets.

    Responsibilities
    -----------------
    - Read expiry date from metadata
    - Calculate expiry state
    - Restrict expired assets
    - Generate expiry notifications.
    """

    @staticmethod
    def get_expiry_date(asset:Asset) -> Optional[date]:
        """
        Reads expiry_data from 
        asset_metadata.business.expiry_date

        Expected format:
        YYYY-MM-DD
        """

        if not asset.asset_metadata:
            return None
        
        try:
            expiry=(
                asset.asset_metadata
                .get("business", {})
                .get("expiry_date")
            )

            if not expiry:
                return None
            
            return datetime.strptime(
                expiry,
                "%Y-%m-%d"
            ).date()
        
        except Exception:
            return None
        

    @staticmethod
    def is_expired(asset:Asset) -> bool:
        expiry=ExpiryService.get_expiry_date(asset)

        if expiry is None:
            return False
        
        return date.today() > expiry
    
    
    @staticmethod
    def days_until_expiry(asset:Asset) -> Optional[int]:
        expiry=ExpiryService.get_expiry_date(asset)

        if expiry is None:
            return False
        
        return (expiry - date.today()).days
    

    @staticmethod
    def is_expiring_soon(asset:Asset, threshold_days: int=30):
        if ExpiryService.is_expired(asset):
            return False
        
        remaining=ExpiryService.days_until_expiry(asset)

        if remaining is None:
            return False
        
        return remaining <= threshold_days
    

    @staticmethod
    def build_expiry_status(
        asset:Asset,
        threshold_days: int=30
    ) -> dict:
        """
        Return computed expiry flags.
        """

        return {
            "expired":ExpiryService.is_expired(asset),
            "expiring_soon":ExpiryService.is_expiring_soon(asset, threshold_days),
            "days_until_theory":ExpiryService.days_until_expiry(asset)
        }
    

    @staticmethod
    def auto_restrict_if_expired(
        asset:Asset,
        db:Session
    ) -> bool:
        
        """
        Automatically restricts expired assets.

        Returns True if asset status changed.
        """

        if not ExpiryService.is_expired(asset):
            return False
        
        if asset.status=="restricted":
            return False
        
        asset.status="restricted"

        admins= (
            db.query(User)
            .filter(
                User.role.in_(["super_admin", "admin"])
            )
            .all()
        )
        
        expiry=ExpiryService.get_expiry_date(asset)

        message=(
            f'Asset "{asset.original_filename}" expired on '
            f"{expiry} and has been automatically restricted."
        )

        for admin in admins:
            db.add(
                Notification(
                    user_id=admin.id,
                    asset_id=asset.id,
                    message=message
                )
            )

            db.commit()
            db.refresh(asset)

            return True
        

    @staticmethod
    def get_expiring_assets(db:Session, threshold_days:int = 30):
        assets=db.query(Asset).all()

        result=[]
        for asset in assets:
            status=ExpiryService.build_expiry_status(
                asset,
                threshold_days
            )

            if status["expired"] or status["expiring_soon"]:
                result.append(
                    {"asset":asset,
                     **status,
                     }
                )

        return result


