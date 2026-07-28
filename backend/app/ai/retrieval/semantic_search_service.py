from sqlalchemy.orm import Session
from sqlalchemy import func
import math
from datetime import datetime, timezone

from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage

from app.ai.embeddings.embedding_utils import (
    embed_asset,
    generate_embedding
)

from app.ai.vectorstore.vector_upsert_service import (
    VectorUpsertService
)

from app.ai.vectorstore.vector_query_service import (
    VectorQueryService
)

# ---------------------------------------------------------
# ENTERPRISE SIMILARITY THRESHOLD
# ---------------------------------------------------------

MINIMUM_SIMILARITY_SCORE = 0.45


# ---------------------------------------------------------
# DISTANCE → SCORE
# ---------------------------------------------------------

def _distance_to_score(
    distance: float
) -> float:

    score = max(
        0.0,
        1.0 - (distance / 2.0)
    )

    return round(score, 4)


# ---------------------------------------------------------
# FETCH ASSETS FROM POSTGRES
# ---------------------------------------------------------

def _fetch_assets_by_ids(
    asset_ids: list[str],
    db: Session
):

    assets = (
        db.query(Asset)
        .filter(Asset.id.in_(asset_ids))
        .all()
    )

    return {
        str(asset.id): asset
        for asset in assets
    }


# ---------------------------------------------------------
# FORMAT + FILTER RESULTS
# ---------------------------------------------------------

def _format_results(
    raw: dict,
    db: Session,
    limit: int,
    approved_only: bool = True,
    filters: dict | None = None,
    query: str | None = None,
    current_user = None,
):

    ids = raw.get("ids", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    if not ids:
        return []

    asset_map = _fetch_assets_by_ids(ids, db)

    # Pre-fetch usage counts for all candidates
    usage_data = db.query(
        AssetUsage.asset_id,
        func.sum(AssetUsage.usage_count).label("total_usage")
    ).filter(
        AssetUsage.asset_id.in_(list(asset_map.keys()))
    ).group_by(
        AssetUsage.asset_id
    ).all()
    
    usage_map = {str(row.asset_id): row.total_usage for row in usage_data}

    formatted_results = []

    for asset_id, distance in zip(ids, distances):

        asset = asset_map.get(asset_id)
        if not asset:
            continue

        # Enforce strict role-based access for non-admins (override approved_only flag)
        user_role = current_user.role if current_user else None
        # if user_role in ["user", "sales_user", "external_partner"]:
        if user_role == "user":
            if asset.status not in ("approved", "published") or not asset.is_latest:
                continue

        # Status filtering (for admins who might optionally pass approved_only=True)
        elif approved_only and asset.status not in ("approved", "published"):
            continue

        # Skip archived assets — hidden from all search results
        if asset.is_archived:
            continue

        # Filter out restricted assets if user is not in the allowed roles list (Phase 4.1)
        if asset.status == "restricted":
            user_role = current_user.role if current_user else None
            if user_role not in ["super_admin", "admin"]:
                meta = asset.asset_metadata or {}
                gov = meta.get("governance") or {}
                allowed_roles = gov.get("restricted_to_roles") or ["admin", "reviewer", "super_admin"]
                if user_role not in allowed_roles:
                    continue

        # Post-filter: geography and status (can't be done in Chroma)
        if filters:
            meta = asset.asset_metadata or {}
            biz = meta.get("business") or {}

            if filters.get("geography") and filters["geography"].lower() not in (biz.get("geography") or "").lower():
                continue

            if filters.get("status") and asset.status != filters["status"]:
                continue

        semantic_score = _distance_to_score(distance)
        if semantic_score < MINIMUM_SIMILARITY_SCORE:
            continue

        # Calculate other ranking metrics
        completeness_score = (asset.completeness_score or 0) / 100.0
        
        now = datetime.now(timezone.utc)
        asset_created = asset.created_at
        days_old = (now - asset_created).days if asset_created else 0
        recency_score = max(0.0, 1.0 - (days_old / 365.0))
        
        usage = usage_map.get(str(asset.id), 0)
        usage_score = min(1.0, math.log(usage + 1) / math.log(100)) if usage > 0 else 0.0
        
        status_score = 1.0 if asset.status in ("approved", "published") else 0.5
        latest_score = 1.0 if asset.is_latest else 0.0
        
        # Calculate composite score
        composite_score = (
            (semantic_score * 0.50) +
            (completeness_score * 0.20) +
            (recency_score * 0.10) +
            (usage_score * 0.10) +
            (status_score * 0.05) +
            (latest_score * 0.05)
        )

        # Build match_explanation
        match_explanation = None
        if query:
            meta = asset.asset_metadata or {}
            ai = meta.get("ai_enrichment") or {}
            tags = ai.get("ai_tags") or []
            desc = (meta.get("mandatory") or {}).get("description") or ""
            q_lower = query.lower()
            reasons = []
            if any(q_lower in str(t).lower() for t in tags):
                reasons.append("matched AI tags")
            if q_lower in desc.lower():
                reasons.append("matched description")
            if ai.get("image_caption") and q_lower in (ai["image_caption"] or "").lower():
                reasons.append("matched AI caption")
            match_explanation = " · ".join(reasons) if reasons else f"semantic similarity {round(semantic_score*100)}%"

        formatted_results.append({
            "asset_id":           str(asset.id),
            "score":              round(composite_score, 4),
            "ranking_breakdown": {
                "semantic_score": round(semantic_score, 4),
                "completeness_score": round(completeness_score, 4),
                "recency_score": round(recency_score, 4),
                "usage_score": round(usage_score, 4),
                "status_score": round(status_score, 4),
                "latest_score": round(latest_score, 4)
            },
            "original_filename":  asset.original_filename,
            "storage_path":       asset.storage_path,
            "thumbnail_path":     asset.thumbnail_path,
            "preview_path":       asset.preview_path,
            "mime_type":          asset.mime_type,
            "status":             asset.status,
            "asset_metadata":     asset.asset_metadata or {},
            "completeness_score": asset.completeness_score or 0,
            "ai_summary":         asset.ai_summary,
            "perceptual_hash":    asset.perceptual_hash,
            "relationship_type":  asset.relationship_type,
            "match_explanation":  match_explanation,
        })

    formatted_results.sort(key=lambda x: x["score"], reverse=True)
    return formatted_results[:limit]


# ---------------------------------------------------------
# MAIN SEARCH SERVICE
# ---------------------------------------------------------

class SemanticSearchService:

    # -----------------------------------------------------
    # INDEX ASSET
    # -----------------------------------------------------

    @staticmethod
    def index_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved"
    ):

        document, embedding = embed_asset(
            asset_metadata
        )

        VectorUpsertService.upsert_embedding(
            asset_id=asset_id,
            embedding=embedding,
            document=document,
            asset=asset_metadata,
            status=status
        )

        return True

    # -----------------------------------------------------
    # REINDEX
    # -----------------------------------------------------

    @staticmethod
    def reindex_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved"
    ):

        return SemanticSearchService.index_asset(
            asset_id,
            asset_metadata,
            status
        )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    @staticmethod
    def search(
        query: str,
        db: Session,
        limit: int = 10,
        approved_only: bool = True,
        filters: dict | None = None,
        search_field: str | None = None,
        current_user = None,
    ):

        # QUERY → EMBEDDING
        query_embedding = generate_embedding(query)

        # ─────────────────────────────────────────────────────────
        # Build Chroma where-clause from facets
        # Chroma supports: $eq, $ne, $gt, $gte, $lt, $lte, $and, $or
        # We store domain, asset_type, language, campaign in metadata
        # ─────────────────────────────────────────────────────────
        where = None
        if filters:
            chroma_filters = []

            if filters.get("domain"):
                chroma_filters.append({"domain": {"$eq": filters["domain"]}})

            if filters.get("asset_type"):
                chroma_filters.append({"asset_type": {"$eq": filters["asset_type"]}})

            if filters.get("language"):
                chroma_filters.append({"language": {"$eq": filters["language"]}})

            if filters.get("campaign"):
                chroma_filters.append({"campaign": {"$eq": filters["campaign"]}})

            if chroma_filters:
                where = chroma_filters[0] if len(chroma_filters) == 1 else {"$and": chroma_filters}

        raw = VectorQueryService.semantic_search(
            query_embedding=query_embedding,
            limit=limit * 5,
            where=where,
        )

        return _format_results(
            raw=raw,
            db=db,
            limit=limit,
            approved_only=approved_only,
            filters=filters,
            query=query,
            current_user=current_user,
        )
