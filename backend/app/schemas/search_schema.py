# # schemas/search_schema.py
# # Request and response schemas for the semantic search API.

# from pydantic import BaseModel, Field
# from typing import Optional, List


# # ---------------------------------------------------------------------------
# # REQUEST
# # ---------------------------------------------------------------------------

# class SemanticSearchRequest(BaseModel):
#     """
#     Body for POST /api/assets/search

#     Example:
#         {
#             "query": "AI landing page banner for enterprise clients",
#             "limit": 10,
#             "approved_only": true,
#             "filters": {
#                 "asset_type": "banner",
#                 "audience": "enterprise"
#             }
#         }
#     """

#     query: str = Field(
#         ...,
#         min_length=1,
#         max_length=500,
#         description="Natural language search query"
#     )

#     limit: int = Field(
#         default=10,
#         ge=1,
#         le=50,
#         description="Maximum number of results to return"
#     )

#     approved_only: bool = Field(
#         default=True,
#         description=(
#             "If true, only return approved assets. "
#             "Admins can set false to search across all statuses."
#         )
#     )

#     filters: Optional[dict] = Field(
#         default=None,
#         description=(
#             "Optional metadata filters. Supported keys: "
#             "asset_type, domain, use_case, audience, funnel_stage, tone. "
#             "Example: {\"domain\": \"ai_services\", \"audience\": \"enterprise\"}"
#         )
#     )


# # ---------------------------------------------------------------------------
# # RESPONSE
# # ---------------------------------------------------------------------------

# class SemanticSearchResult(BaseModel):
#     """Single asset result returned by semantic search."""

#     asset_id: str
#     score: float = Field(description="Relevance score 0-1, higher is better")
#     asset_name: str
#     asset_type: str
#     domain: str
#     use_case: str
#     audience: str
#     funnel_stage: str
#     tone: str
#     owner: str
#     status: str
#     ai_tags: List[str]
#     image_caption: str


# class SemanticSearchResponse(BaseModel):
#     """Response envelope for semantic search."""

#     query: str
#     total: int
#     results: List[SemanticSearchResult]
# schemas/search_schema.py
# Request and response schemas for semantic search endpoints.

from pydantic import BaseModel, Field
from typing import Optional, List


# ---------------------------------------------------------------------------
# TEXT SEARCH — request/response
# ---------------------------------------------------------------------------

class SemanticSearchRequest(BaseModel):
    """Body for POST /api/assets/search"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query"
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )

    approved_only: bool = Field(
        default=True,
        description="If true, only return approved assets"
    )

    filters: Optional[dict] = Field(
        default=None,
        description=(
            "Optional metadata filters. Supported keys: "
            "asset_type, domain, use_case, audience, funnel_stage, tone. "
            "Example: {\"domain\": \"ai_services\", \"audience\": \"enterprise\"}"
        )
    )


class SemanticSearchResult(BaseModel):
    """Single asset result from text search."""

    asset_id: str
    score: float = Field(description="Relevance score 0-1, higher is better")
    asset_name: str
    asset_type: str
    domain: str
    use_case: str
    audience: str
    funnel_stage: str
    tone: str
    owner: str
    status: str
    ai_tags: List[str]
    image_caption: str


class SemanticSearchResponse(BaseModel):
    """Response for POST /api/assets/search"""

    query: str
    total: int
    results: List[SemanticSearchResult]


# ---------------------------------------------------------------------------
# FILE SEARCH — response
# (request is multipart/form-data — defined via FastAPI Form params)
# ---------------------------------------------------------------------------

class FileSearchResult(BaseModel):
    """Single asset result from file search."""

    asset_id: str
    score: float = Field(description="Relevance score 0-1, higher is better")
    asset_name: str
    asset_type: str
    domain: str
    use_case: str
    audience: str
    funnel_stage: str
    tone: str
    owner: str
    status: str
    ai_tags: List[str]
    image_caption: str


class FileSearchResponse(BaseModel):
    """
    Response for POST /api/assets/search/file

    Includes what the AI extracted from the uploaded file
    so the user can see why these results were returned.
    """

    filename: str = Field(description="Name of the uploaded search file")

    extracted_tags: List[str] = Field(
        description="AI tags extracted from the uploaded file"
    )

    extracted_text: str = Field(
        default="",
        description="Text extracted from the file (OCR / PDF text)"
    )

    image_caption: str = Field(
        default="",
        description="Caption generated for images/videos"
    )

    total: int = Field(description="Number of matching assets found")

    results: List[FileSearchResult] = Field(
        description="Matching assets ranked by similarity score"
    )