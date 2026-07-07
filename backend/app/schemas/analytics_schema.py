from pydantic import BaseModel
from typing import List
from app.schemas.asset_schema import AssetResponse

class UnusedAssetsResponse(BaseModel):
    total: int
    days_threshold: int
    items: List[AssetResponse]
