from pydantic import BaseModel, Field
from typing import Optional, List


# ---------------------------------------------------------------------------
# SHARED RESULT — full asset data for frontend
# ---------------------------------------------------------------------------

class BaseSearchResult(BaseModel):
    asset_id:          str
    original_filename: str
    storage_path:      str
    thumbnail_path:    Optional[str] = None
    preview_path:      Optional[str] = None
    mime_type:         str
    status:            str
    asset_metadata:    dict


# ---------------------------------------------------------------------------
# SEMANTIC SEARCH
# ---------------------------------------------------------------------------

class SemanticSearchRequest(BaseModel):
    query:         str  = Field(..., min_length=1, max_length=500)
    limit:         int  = Field(default=10, ge=1, le=50)
    approved_only: bool = Field(default=True)
    filters: Optional[dict] = Field(
        default = None,
        description=(
            "Optional metadata filters "
            "(domain, audience, use_case, asset_type)"
        )
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


class HybridSearchResult(BaseSearchResult):
    hybrid_score:   float = Field(description="Combined score 0-1")
    semantic_score: float = Field(description="Semantic similarity 0-1")
    keyword_score:  float = Field(description="Keyword match 0-1")


class HybridSearchResponse(BaseModel):
    query:   str
    total:   int
    results: List[HybridSearchResult]