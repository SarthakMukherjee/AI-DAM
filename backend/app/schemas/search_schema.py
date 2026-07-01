from pydantic import BaseModel, Field
from typing import Optional, List


# ---------------------------------------------------------------------------
# SHARED RESULT — full asset data for frontend
# ---------------------------------------------------------------------------

class BaseSearchResult(BaseModel):
    asset_id:             str
    original_filename:    str
    storage_path:         str
    thumbnail_path:       Optional[str] = None
    preview_path:         Optional[str] = None
    mime_type:            str
    status:               str
    asset_metadata:       dict
    # Queryable AI columns exposed in results
    completeness_score:   int = 0
    ai_summary:           Optional[str] = None
    perceptual_hash:      Optional[str] = None
    # Ranking explanation
    match_explanation:    Optional[str] = None


# ---------------------------------------------------------------------------
# FACETED FILTER — shared across all search endpoints
# ---------------------------------------------------------------------------

class SearchFilters(BaseModel):
    """
    Optional faceted filters applied to both keyword and semantic search.
    All fields are optional — omitting a field means no restriction on it.
    """
    domain:      Optional[str] = None
    status:      Optional[str] = None
    asset_type:  Optional[str] = None
    geography:   Optional[str] = None
    campaign:    Optional[str] = None
    language:    Optional[str] = None


# ---------------------------------------------------------------------------
# SEMANTIC SEARCH
# ---------------------------------------------------------------------------

class SemanticSearchRequest(BaseModel):
    query:         str  = Field(..., min_length=1, max_length=500)
    limit:         int  = Field(default=10, ge=1, le=50)
    approved_only: bool = Field(default=True)
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional faceted filters (domain, status, asset_type, geography, campaign, language)"
    )
    search_field: Optional[str] = Field(
        default=None,
        description="Scope search to a specific metadata field, e.g. 'campaign', 'description', 'ai_tags'"
    )


class SemanticSearchResult(BaseSearchResult):
    score: float = Field(description="Relevance score 0-1")


class SemanticSearchResponse(BaseModel):
    query:   str
    total:   int
    results: List[SemanticSearchResult]


# ---------------------------------------------------------------------------
# HYBRID SEARCH
# ---------------------------------------------------------------------------

class HybridSearchRequest(BaseModel):
    query:         str  = Field(..., min_length=1, max_length=500)
    limit:         int  = Field(default=10, ge=1, le=50)
    approved_only: bool = Field(default=True)
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional faceted filters"
    )
    search_field: Optional[str] = Field(
        default=None,
        description="Scope search to a specific metadata field"
    )


class HybridSearchResult(BaseSearchResult):
    hybrid_score:   float = Field(description="Combined score 0-1")
    semantic_score: float = Field(description="Semantic similarity 0-1")
    keyword_score:  float = Field(description="Keyword match 0-1")


class HybridSearchResponse(BaseModel):
    query:   str
    total:   int
    results: List[HybridSearchResult]