from pydantic import BaseModel
from typing import List
from app.schemas.asset_schema import AssetResponse

class UnusedAssetsResponse(BaseModel):
    total: int
    days_threshold: int
    items: List[AssetResponse]

# new addition on 07-07-26
class MissingMetadataResponse(BaseModel):
    total: int
    threshold: int
    items: List[AssetResponse]

class ApprovalTimeMetrics(BaseModel):
    average_hours: float
    total_approved: int
    total_rejected: int

class ApprovalTimeResponse(BaseModel):
    global_metrics: ApprovalTimeMetrics
    by_domain: dict[str, float]

class SearchGapItem(BaseModel):
    query: str
    search_type: str
    count: int
    avg_results: float

class SearchGapResponse(BaseModel):
    items: List[SearchGapItem]
