# # # # schemas/search_schema.py
# # # # Request and response schemas for the semantic search API.

# # # from pydantic import BaseModel, Field
# # # from typing import Optional, List


# # # # ---------------------------------------------------------------------------
# # # # REQUEST
# # # # ---------------------------------------------------------------------------

# # # class SemanticSearchRequest(BaseModel):
# # #     """
# # #     Body for POST /api/assets/search

# # #     Example:
# # #         {
# # #             "query": "AI landing page banner for enterprise clients",
# # #             "limit": 10,
# # #             "approved_only": true,
# # #             "filters": {
# # #                 "asset_type": "banner",
# # #                 "audience": "enterprise"
# # #             }
# # #         }
# # #     """

# # #     query: str = Field(
# # #         ...,
# # #         min_length=1,
# # #         max_length=500,
# # #         description="Natural language search query"
# # #     )

# # #     limit: int = Field(
# # #         default=10,
# # #         ge=1,
# # #         le=50,
# # #         description="Maximum number of results to return"
# # #     )

# # #     approved_only: bool = Field(
# # #         default=True,
# # #         description=(
# # #             "If true, only return approved assets. "
# # #             "Admins can set false to search across all statuses."
# # #         )
# # #     )

# # #     filters: Optional[dict] = Field(
# # #         default=None,
# # #         description=(
# # #             "Optional metadata filters. Supported keys: "
# # #             "asset_type, domain, use_case, audience, funnel_stage, tone. "
# # #             "Example: {\"domain\": \"ai_services\", \"audience\": \"enterprise\"}"
# # #         )
# # #     )


# # # # ---------------------------------------------------------------------------
# # # # RESPONSE
# # # # ---------------------------------------------------------------------------

# # # class SemanticSearchResult(BaseModel):
# # #     """Single asset result returned by semantic search."""

# # #     asset_id: str
# # #     score: float = Field(description="Relevance score 0-1, higher is better")
# # #     asset_name: str
# # #     asset_type: str
# # #     domain: str
# # #     use_case: str
# # #     audience: str
# # #     funnel_stage: str
# # #     tone: str
# # #     owner: str
# # #     status: str
# # #     ai_tags: List[str]
# # #     image_caption: str


# # # class SemanticSearchResponse(BaseModel):
# # #     """Response envelope for semantic search."""

# # #     query: str
# # #     total: int
# # #     results: List[SemanticSearchResult]
# # # schemas/search_schema.py
# # # Request and response schemas for semantic search endpoints.

# # from pydantic import BaseModel, Field
# # from typing import Optional, List


# # # ---------------------------------------------------------------------------
# # # TEXT SEARCH — request/response
# # # ---------------------------------------------------------------------------

# # class SemanticSearchRequest(BaseModel):
# #     """Body for POST /api/assets/search"""

# #     query: str = Field(
# #         ...,
# #         min_length=1,
# #         max_length=500,
# #         description="Natural language search query"
# #     )

# #     limit: int = Field(
# #         default=10,
# #         ge=1,
# #         le=50,
# #         description="Maximum number of results to return"
# #     )

# #     approved_only: bool = Field(
# #         default=True,
# #         description="If true, only return approved assets"
# #     )

# #     filters: Optional[dict] = Field(
# #         default=None,
# #         description=(
# #             "Optional metadata filters. Supported keys: "
# #             "asset_type, domain, use_case, audience, funnel_stage, tone. "
# #             "Example: {\"domain\": \"ai_services\", \"audience\": \"enterprise\"}"
# #         )
# #     )


# # class SemanticSearchResult(BaseModel):
# #     """Single asset result from text search."""

# #     asset_id: str
# #     score: float = Field(description="Relevance score 0-1, higher is better")

# #     # POSTGRES DATA

# #     original_filename: str

# #     storage_path: str

# #     thumbnail_path: Optional[str] = None

# #     preview_path: Optional[str] = None

# #     mime_type: str

# #     status: str

# #     # FULL METADATA
# #     asset_metadata: dict


# # class SemanticSearchResponse(BaseModel):
# #     """Response for POST /api/assets/search"""

# #     query: str
# #     total: int
# #     results: List[SemanticSearchResult]


# # # ---------------------------------------------------------------------------
# # # FILE SEARCH — response
# # # (request is multipart/form-data — defined via FastAPI Form params)
# # # ---------------------------------------------------------------------------

# # # class FileSearchResult(BaseModel):
# # #     """Single asset result from file search."""

# # #     asset_id: str
# # #     score: float = Field(description="Relevance score 0-1, higher is better")
# # #     asset_name: str
# # #     asset_type: str
# # #     domain: str
# # #     use_case: str
# # #     audience: str
# # #     funnel_stage: str
# # #     tone: str
# # #     owner: str
# # #     status: str
# # #     ai_tags: List[str]
# # #     image_caption: str


# # # class FileSearchResponse(BaseModel):
# # #     """
# # #     Response for POST /api/assets/search/file

# # #     Includes what the AI extracted from the uploaded file
# # #     so the user can see why these results were returned.
# # #     """

# # #     filename: str = Field(description="Name of the uploaded search file")

# # #     extracted_tags: List[str] = Field(
# # #         description="AI tags extracted from the uploaded file"
# # #     )

# # #     extracted_text: str = Field(
# # #         default="",
# # #         description="Text extracted from the file (OCR / PDF text)"
# # #     )

# # #     image_caption: str = Field(
# # #         default="",
# # #         description="Caption generated for images/videos"
# # #     )

# # #     total: int = Field(description="Number of matching assets found")

# # #     results: List[FileSearchResult] = Field(
# # #         description="Matching assets ranked by similarity score"
# # #     )

# # api/routes/search_routes.py
# # Search endpoints for the DAM system.
# #
# # Routes:
# #   POST /api/assets/search          — semantic search
# #   POST /api/assets/search/hybrid   — hybrid search (keyword + semantic)
# #   POST /api/assets/search/file     — file upload semantic search
# #   POST /api/assets/{id}/reindex    — reindex single asset

# import json

# from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
# from sqlalchemy.orm import Session

# from app.api.dependencies.database import get_db
# from app.models.asset.asset_model import Asset

# from app.ai.embeddings.semantic_search_service import SemanticSearchService
# from app.ai.embeddings.hybrid_search_service import HybridSearchService
# from app.ai.embeddings.file_search_service import FileSearchService

# from app.schemas.search_schema import (
#     SemanticSearchRequest,
#     SemanticSearchResponse,
#     SemanticSearchResult,
#     HybridSearchRequest,
#     HybridSearchResponse,
#     HybridSearchResult,
#     FileSearchResponse,
#     FileSearchResult,
# )

# router = APIRouter(
#     prefix="/api/assets",
#     tags=["Search"],
# )


# # ---------------------------------------------------------------------------
# # POST /api/assets/search — semantic search
# # ---------------------------------------------------------------------------

# @router.post(
#     "/search",
#     response_model=SemanticSearchResponse,
#     summary="Semantic Search",
#     description="Search DAM assets using natural language. Returns full asset data ranked by semantic similarity.",
# )
# async def semantic_search(
#     body: SemanticSearchRequest,
#     db: Session = Depends(get_db),
# ):
#     try:
#         raw_results = SemanticSearchService.search(
#             query=body.query,
#             db=db,
#             limit=body.limit,
#             approved_only=body.approved_only,
#             filters=body.filters,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

#     results = [SemanticSearchResult(**r) for r in raw_results]
#     return SemanticSearchResponse(query=body.query, total=len(results), results=results)


# # ---------------------------------------------------------------------------
# # POST /api/assets/search/hybrid — hybrid search
# # ---------------------------------------------------------------------------

# @router.post(
#     "/search/hybrid",
#     response_model=HybridSearchResponse,
#     summary="Hybrid Search",
#     description=(
#         "Combines keyword search (PostgreSQL) and semantic search (ChromaDB). "
#         "Results merged and re-ranked. hybrid_score = semantic*0.6 + keyword*0.4."
#     ),
# )
# async def hybrid_search(
#     body: HybridSearchRequest,
#     db: Session = Depends(get_db),
# ):
#     try:
#         raw_results = HybridSearchService.search(
#             query=body.query,
#             db=db,
#             limit=body.limit,
#             approved_only=body.approved_only,
#             filters=body.filters,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

#     results = [HybridSearchResult(**r) for r in raw_results]
#     return HybridSearchResponse(query=body.query, total=len(results), results=results)


# # ---------------------------------------------------------------------------
# # POST /api/assets/search/file — file upload search
# # ---------------------------------------------------------------------------

# @router.post(
#     "/search/file",
#     response_model=FileSearchResponse,
#     summary="File Semantic Search",
#     description="Upload a file to find similar assets. File is NOT stored.",
# )
# async def search_by_file(
#     file: UploadFile = File(...),
#     limit: int = Form(default=10, ge=1, le=50),
#     approved_only: bool = Form(default=True),
#     filters: str = Form(default=None),
#     db: Session = Depends(get_db),
# ):
#     parsed_filters = None
#     if filters:
#         try:
#             parsed_filters = json.loads(filters)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="filters must be a valid JSON string")

#     try:
#         file_bytes = await file.read()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

#     if not file_bytes:
#         raise HTTPException(status_code=400, detail="Uploaded file is empty")

#     try:
#         result = FileSearchService().search_by_file(
#             file_bytes=file_bytes,
#             filename=file.filename,
#             limit=limit,
#             approved_only=approved_only,
#             filters=parsed_filters,
#             db=db,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"File search failed: {str(e)}")

#     if result.get("error"):
#         raise HTTPException(status_code=422, detail=result["error"])

#     results = [FileSearchResult(**r) for r in result["results"]]
#     return FileSearchResponse(
#         filename=result["filename"],
#         extracted_tags=result["enrichment"].get("ai_tags", []),
#         extracted_text=result["enrichment"].get("extracted_text", ""),
#         image_caption=result["enrichment"].get("image_caption", ""),
#         total=result["total"],
#         results=results,
#     )


# # ---------------------------------------------------------------------------
# # POST /api/assets/{asset_id}/reindex
# # ---------------------------------------------------------------------------

# @router.post(
#     "/{asset_id}/reindex",
#     summary="Reindex Asset",
#     description="Reindex a single asset in ChromaDB. Admin only.",
# )
# async def reindex_asset(
#     asset_id: str,
#     db: Session = Depends(get_db),
# ):
#     asset = db.query(Asset).filter(Asset.id == asset_id).first()

#     if not asset:
#         raise HTTPException(status_code=404, detail="Asset not found")

#     if not asset.asset_metadata:
#         raise HTTPException(status_code=400, detail="Asset has no metadata to index")

#     try:
#         SemanticSearchService.reindex_asset(
#             asset_id=str(asset.id),
#             asset_metadata=asset.asset_metadata,
#             status=asset.status,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

#     return {
#         "message": f"Asset {asset_id} reindexed successfully",
#         "asset_id": asset_id,
#         "status":   asset.status,
#     }
# schemas/search_schema.py

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