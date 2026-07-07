import traceback

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import get_current_user, require_admin
from app.models.user.user_model import User
from app.models.asset.asset_model import Asset
from app.models.analytics.search_log_model import SearchLog

from app.ai.retrieval.semantic_search_service import SemanticSearchService
from app.ai.retrieval.hybrid_search_service import HybridSearchService

from app.schemas.search_schema import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    HybridSearchRequest,
    HybridSearchResponse,
    HybridSearchResult,
)

router = APIRouter(
    prefix="/api/assets",
    tags=["Search"],
)


# ---------------------------------------------------------------------------
# POST /api/assets/search — semantic search
# ---------------------------------------------------------------------------

@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Semantic Search",
    description="Search DAM assets using natural language. Returns approved assets ranked by semantic similarity.",
)
async def semantic_search(
    body: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FLOW:
    User Query → Embedding → ChromaDB → Asset IDs → PostgreSQL Fetch → Results
    """
    try:
        raw_results = SemanticSearchService.search(
            db=db,
            query=body.query,
            limit=body.limit,
            approved_only=body.approved_only,
            filters=body.filters.model_dump(exclude_none=True) if body.filters else None,
            search_field=body.search_field,
            current_user=current_user,
        )

    except Exception as e:
        print("SEMANTIC SEARCH ERROR")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )

    results = [SemanticSearchResult(**r) for r in raw_results]
    
    # Log the search
    try:
        search_log = SearchLog(
            query=body.query,
            search_type="semantic",
            results_count=len(results),
            user_id=current_user.id
        )
        db.add(search_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log semantic search: {e}")
        db.rollback()

    return SemanticSearchResponse(
        query=body.query,
        total=len(results),
        results=results,
    )


# ---------------------------------------------------------------------------
# POST /api/assets/search/hybrid — hybrid search
# ---------------------------------------------------------------------------

@router.post(
    "/search/hybrid",
    response_model=HybridSearchResponse,
    summary="Hybrid Search",
    description=(
        "Combines keyword search (PostgreSQL) + semantic search (ChromaDB). "
        "Results merged and re-ranked. "
        "hybrid_score = semantic_score × 0.6 + keyword_score × 0.4"
    ),
)
async def hybrid_search(
    body: HybridSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        raw_results = HybridSearchService.search(
            db=db,
            query=body.query,
            limit=body.limit,
            approved_only=body.approved_only,
            filters=body.filters.model_dump(exclude_none=True) if body.filters else None,
            search_field=body.search_field,
            current_user=current_user,
        )

    except Exception as e:
        print("HYBRID SEARCH ERROR")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Hybrid search failed: {str(e)}"
        )

    results = [HybridSearchResult(**r) for r in raw_results]
    
    # Log the search
    try:
        search_log = SearchLog(
            query=body.query,
            search_type="hybrid",
            results_count=len(results),
            user_id=current_user.id
        )
        db.add(search_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log hybrid search: {e}")
        db.rollback()

    return HybridSearchResponse(
        query=body.query,
        total=len(results),
        results=results,
    )


# ---------------------------------------------------------------------------
# POST /api/assets/{asset_id}/reindex
# ---------------------------------------------------------------------------

@router.post(
    "/{asset_id}/reindex",
    summary="Reindex Asset",
    description="Reindex a single asset in ChromaDB. Admin only.",
)
async def reindex_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.asset_metadata:
        raise HTTPException(status_code=400, detail="Asset has no metadata to index")

    try:
        SemanticSearchService.reindex_asset(
            asset_id=str(asset.id),
            asset_metadata=asset.asset_metadata,
            status=asset.status,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

    return {
        "message": f"Asset {asset_id} reindexed successfully",
        "asset_id": asset_id,
        "status":   asset.status,
    }