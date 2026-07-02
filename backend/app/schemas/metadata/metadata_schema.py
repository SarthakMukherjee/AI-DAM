from pydantic import BaseModel, Field
from typing import List, Optional

from app.schemas.metadata.metadata_enums import (
    AssetStatus,
    AssetTypes,
    DomainType,
    UseCaseTypes,
    AudienceType,
    FunnelStage,
    ToneType,
    UsageRightsType,
)

# MANDATORY METADATA

class MandatoryMetadata(BaseModel):
    asset_name: str
    asset_type: AssetTypes
    description: str
    created_by: str
    usage_rights: UsageRightsType
    owner: str

# BUSINESS METADATA
class BusinessMetadata(BaseModel):
    domain: DomainType
    use_case: UseCaseTypes
    audience: AudienceType
    funnel_stage: FunnelStage
    # Extended metadata fields (all optional, backward-compatible)
    service_line: Optional[str] = ""
    geography: Optional[str] = ""
    campaign: Optional[str] = ""
    language: Optional[str] = ""
    channel: Optional[str] = ""
    expiry_date: Optional[str] = ""


# CONTENT METADATA
class ContentMetadata(BaseModel):
    keywords: Optional[List[str]] = []
    visual_elements: Optional[List[str]] = []
    tone: ToneType


# AI ENRICHMENT METADATA
class AIEnrichmentMetadata(BaseModel):
    ai_tags: Optional[List[str]] = []
    extracted_text: Optional[str] = None
    image_caption: Optional[str] = None
    detected_objects: Optional[List[str]] = []
    searchable_tags: Optional[List[str]] = []
    enrichment_status: Optional[str] = ""
    # Clean LLM-generated summary stored separately for search & display
    ai_summary: Optional[str] = None


# FINAL ASSET METADATA
class AssetMetadataSchema(BaseModel):
    mandatory: MandatoryMetadata
    business: BusinessMetadata
    content: ContentMetadata
    ai_enrichment: Optional[AIEnrichmentMetadata] = AIEnrichmentMetadata()
