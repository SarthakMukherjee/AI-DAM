# # api/search_route.py
# # Semantic search endpoints for the DAM system.
# #
# # Routes:
# #   POST /api/assets/search          — main semantic search
# #   POST /api/assets/{id}/reindex    — reindex a single asset (Admin only)

# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session

# from app.core.db import get_db
# from app.models.asset.asset_model import Asset

# from app.ai.embeddings.semantic_search_service import SemanticSearchService

# from app.schemas.search_schema import (
#     SemanticSearchRequest,
#     SemanticSearchResponse,
#     SemanticSearchResult,
# )

# router = APIRouter(
#     prefix="/api/assets",
#     tags=["Semantic Search"],
# )


# # ---------------------------------------------------------------------------
# # POST /api/assets/search
# # ---------------------------------------------------------------------------

# @router.post(
#     "/search",
#     response_model=SemanticSearchResponse,
#     summary="Semantic Search",
#     description=(
#         "Search DAM assets using natural language. "
#         "Returns approved assets ranked by semantic similarity. "
#         "Supports optional metadata filters (asset_type, domain, audience, etc.)."
#     ),
# )
# async def semantic_search(
#     body: SemanticSearchRequest,
# ):
#     """
#     Main semantic search endpoint.

#     Any authenticated user can search.
#     Only approved assets are returned by default (approved_only=True).

#     Example request:
#         POST /api/assets/search
#         {
#             "query": "Homepage AI banner for enterprise audience",
#             "limit": 10,
#             "approved_only": true,
#             "filters": { "asset_type": "banner" }
#         }

#     Example response:
#         {
#             "query": "Homepage AI banner for enterprise audience",
#             "total": 3,
#             "results": [
#                 {
#                     "asset_id": "uuid",
#                     "score": 0.91,
#                     "asset_name": "AI Hero Banner v2",
#                     "asset_type": "banner",
#                     ...
#                 }
#             ]
#         }
#     """
#     try:
#         raw_results = SemanticSearchService.search(
#             query=body.query,
#             limit=body.limit,
#             approved_only=body.approved_only,
#             filters=body.filters,
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Semantic search failed: {str(e)}"
#         )

#     results = [SemanticSearchResult(**r) for r in raw_results]

#     return SemanticSearchResponse(
#         query=body.query,
#         total=len(results),
#         results=results,
#     )


# # ---------------------------------------------------------------------------
# # POST /api/assets/{asset_id}/reindex
# # ---------------------------------------------------------------------------

# @router.post(
#     "/{asset_id}/reindex",
#     summary="Reindex Asset",
#     description=(
#         "Reindex a single asset in the vector store. "
#         "Use this if semantic indexing failed during upload, "
#         "or after manually updating asset metadata. Admin only."
#     ),
# )
# async def reindex_asset(
#     asset_id: str,
#     db: Session = Depends(get_db),
# ):
#     """
#     Manually triggers reindexing of an asset into ChromaDB.

#     Use cases:
#     - Semantic indexing failed silently during upload
#     - Metadata was manually edited in the DB
#     - Bulk reindex after a schema change

#     Returns 404 if asset doesn't exist.
#     Returns 400 if asset has no metadata to index.
#     """

#     asset = (
#         db.query(Asset)
#         .filter(Asset.id == asset_id)
#         .first()
#     )

#     if not asset:
#         raise HTTPException(status_code=404, detail="Asset not found")

#     if not asset.asset_metadata:
#         raise HTTPException(
#             status_code=400,
#             detail="Asset has no metadata to index"
#         )

#     try:
#         SemanticSearchService.reindex_asset(
#             asset_id=str(asset.id),
#             asset=asset.asset_metadata,
#             status=asset.status,
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Reindex failed: {str(e)}"
#         )

#     return {
#         "message": f"Asset {asset_id} reindexed successfully",
#         "asset_id": asset_id,
#         "status": asset.status,
#     }
# api/routes/search_routes.py
# Semantic search endpoints for the DAM system.
#
# Routes:
#   POST /api/assets/search              — text-based semantic search
#   POST /api/assets/search/file         — file upload semantic search
#   POST /api/assets/{asset_id}/reindex  — reindex a single asset (Admin only)

import json

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

# from app.core.db import get_db
from app.api.dependencies.database import get_db
from app.models.asset.asset_model import Asset

from app.ai.embeddings.semantic_search_service import SemanticSearchService
from app.ai.embeddings.file_search_service import FileSearchService

from app.schemas.search_schema import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    FileSearchResponse,
    FileSearchResult,
)

router = APIRouter(
    prefix="/api/assets",
    tags=["Semantic Search"],
)


# ---------------------------------------------------------------------------
# POST /api/assets/search
# Text-based semantic search
# ---------------------------------------------------------------------------

@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Text Semantic Search",
    description=(
        "Search DAM assets using natural language query. "
        "Returns approved assets ranked by semantic similarity."
    ),
)
async def semantic_search(
    body: SemanticSearchRequest,
):
    try:
        raw_results = SemanticSearchService.search(
            query=body.query,
            limit=body.limit,
            approved_only=body.approved_only,
            filters=body.filters,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )

    results = [SemanticSearchResult(**r) for r in raw_results]

    return SemanticSearchResponse(
        query=body.query,
        total=len(results),
        results=results,
    )


# ---------------------------------------------------------------------------
# POST /api/assets/search/file
# File upload semantic search
# ---------------------------------------------------------------------------

@router.post(
    "/search/file",
    response_model=FileSearchResponse,
    summary="File Semantic Search",
    description=(
        "Upload an image, PDF, or video to find similar assets in the DAM. "
        "The file is processed through the AI enrichment pipeline "
        "(same as upload) to extract tags, then matched against stored vectors. "
        "The uploaded file is NOT stored — it is only used for search."
    ),
)
async def search_by_file(
    file: UploadFile = File(
        ...,
        description="Image (jpg/png/webp/gif), PDF, or Video (mp4/mov/avi/mkv/webm)"
    ),
    limit: int = Form(
        default=10,
        ge=1,
        le=50,
        description="Max results to return"
    ),
    approved_only: bool = Form(
        default=True,
        description="Only return approved assets"
    ),
    filters: str = Form(
        default=None,
        description=(
            "Optional JSON string of metadata filters. "
            "e.g. '{\"asset_type\": \"banner\", \"domain\": \"ai_services\"}'"
        )
    ),
):
    """
    File-based semantic search.

    How it works:
    1. Uploaded file runs through the AI enrichment pipeline
       (caption, object detection, OCR/text extraction, LLM tagging)
    2. Extracted tags are embedded into a vector
    3. Vector is matched against all stored asset vectors in ChromaDB
    4. Most similar assets are returned ranked by relevance score

    The uploaded file is processed in memory and deleted immediately —
    it is never stored in the DAM.

    Supported formats:
    - Images: jpg, jpeg, png, webp, gif
    - Documents: pdf
    - Videos: mp4, mov, avi, mkv, webm
    """

    # Parse filters from JSON string (Form data can't send dicts directly)
    parsed_filters = None
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="filters must be a valid JSON string"
            )

    # Read file bytes
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    # Run file search pipeline
    try:
        search_service = FileSearchService()

        result = search_service.search_by_file(
            file_bytes=file_bytes,
            filename=file.filename,
            limit=limit,
            approved_only=approved_only,
            filters=parsed_filters,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File search failed: {str(e)}"
        )

    # Handle unsupported file type
    if result.get("error"):
        raise HTTPException(
            status_code=422,
            detail=result["error"]
        )

    results = [FileSearchResult(**r) for r in result["results"]]

    return FileSearchResponse(
        filename=result["filename"],
        extracted_tags=result["enrichment"].get("ai_tags", []),
        extracted_text=result["enrichment"].get("extracted_text", ""),
        image_caption=result["enrichment"].get("image_caption", ""),
        total=result["total"],
        results=results,
    )


# ---------------------------------------------------------------------------
# POST /api/assets/{asset_id}/reindex
# ---------------------------------------------------------------------------

@router.post(
    "/{asset_id}/reindex",
    summary="Reindex Asset",
    description=(
        "Reindex a single asset in the vector store. "
        "Use this if semantic indexing failed during upload, "
        "or after manually updating asset metadata. Admin only."
    ),
)
async def reindex_asset(
    asset_id: str,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.asset_metadata:
        raise HTTPException(
            status_code=400,
            detail="Asset has no metadata to index"
        )

    try:
        SemanticSearchService.reindex_asset(
            asset_id=str(asset.id),
            asset=asset.asset_metadata,
            status=asset.status,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reindex failed: {str(e)}"
        )

    return {
        "message": f"Asset {asset_id} reindexed successfully",
        "asset_id": asset_id,
        "status": asset.status,
    }