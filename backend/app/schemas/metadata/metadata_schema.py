from pydantic import BaseModel, Field
from typing import List, Optional

from app.schemas.metadata.metadata_enums import (
    AssetStatus,
    AssetTypes,
    DomainType,
    UseCaseTypes,
    AudienceType,
    FunnelStage,
    ToneType
)

# MANDATORY METADATA

class MandatoryMetadata(BaseModel):
    asset_name: str
    asset_type: AssetTypes
    description: str
    created_by: str
    usage_rights: str
    owner: str

# BUSINEES METADATA
class BusinessMetadata(BaseModel):
    domain: DomainType
    use_case: UseCaseTypes
    audience: AudienceType
    funnel_stage: FunnelStage


# CONTENT METADATA
class ContentMetadata(BaseModel):
    keywords: Optional[List[str]] = []
    visual_elements: Optional[List[str]] = []
    tone: ToneType

# AI TAG  STRUCTURE
# class AITag(BaseModel):
#     tag: str
#     confidence: float
#     source: str


# AI ENRICHMENT METADATA
class AIEnrichmentMetadata(BaseModel):
    ai_tags: Optional[List[str]] = []
    extracted_text: Optional[str] = None
    image_caption: Optional[str] = None
    detected_objects: Optional[List[str]] = []
    searchable_tags: Optional[List[str]] = []
    enrichment_status: Optional[str] = ""


# FINAL ASSET METADATA
class AssetMetadataSchema(BaseModel):
    mandatory: MandatoryMetadata
    business: BusinessMetadata
    content: ContentMetadata
    ai_enrichment: Optional[AIEnrichmentMetadata] = AIEnrichmentMetadata()

