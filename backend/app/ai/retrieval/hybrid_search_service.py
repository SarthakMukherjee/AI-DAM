from sqlalchemy.orm import Session

from app.ai.retrieval.semantic_search_service import SemanticSearchService
from app.ai.retrieval.keyword_search_service import KeywordSearchService

SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT  = 0.4


class HybridSearchService:

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 10,
        approved_only: bool = True,
        filters: dict | None = None,
        search_field: str | None = None,
        current_user = None,
    ) -> list[dict]:
        """
        Hybrid search: keyword + semantic, merged and re-ranked.

        Args:
            db:            SQLAlchemy session
            query:         User search string
            limit:         Final number of results
            approved_only: Only approved assets
            filters:       Faceted filter dict (domain, status, asset_type, etc.)
            search_field:  Optional scope to a specific metadata field
            current_user:  Authenticated user object for role filtering

        Returns:
            List of result dicts sorted by hybrid_score descending.
        """

        fetch_limit = limit * 3

        # 1. KEYWORD — PostgreSQL (with facets + field scoping)
        keyword_results = KeywordSearchService.search(
            db=db,
            query=query,
            limit=fetch_limit,
            approved_only=approved_only,
            filters=filters,
            search_field=search_field,
            current_user=current_user,
        )

        # 2. SEMANTIC — ChromaDB + PostgreSQL (with facets)
        semantic_results = SemanticSearchService.search(
            query=query,
            db=db,
            limit=fetch_limit,
            approved_only=approved_only,
            filters=filters,
            search_field=search_field,
            current_user=current_user,
        )

        # 3. MERGE + RE-RANK
        return _merge_and_rank(keyword_results, semantic_results, limit)


def _merge_and_rank(
    keyword_results: list[dict],
    semantic_results: list[dict],
    limit: int,
) -> list[dict]:

    merged: dict[str, dict] = {}

    # Index keyword results
    for r in keyword_results:
        asset_id = r["asset_id"]
        merged[asset_id] = {
            **r,
            "keyword_score":  r.get("keyword_score", 0.0),
            "semantic_score": 0.0,
        }

    # Merge semantic results
    for r in semantic_results:
        asset_id = r["asset_id"]
        if asset_id in merged:
            # Found in both — add semantic score
            merged[asset_id]["semantic_score"] = r.get("score", 0.0)
        else:
            # Only in semantic
            merged[asset_id] = {
                **r,
                "keyword_score":  0.0,
                "semantic_score": r.get("score", 0.0),
            }

    # Compute hybrid score for all
    results = []
    for asset_id, data in merged.items():
        hybrid_score = round(
            (data["semantic_score"] * SEMANTIC_WEIGHT) +
            (data["keyword_score"]  * KEYWORD_WEIGHT),
            4
        )
        results.append({
            "asset_id":          asset_id,
            "hybrid_score":      hybrid_score,
            "semantic_score":    round(data["semantic_score"], 4),
            "keyword_score":     round(data["keyword_score"], 4),
            "original_filename": data.get("original_filename", ""),
            "storage_path":      data.get("storage_path", ""),
            "thumbnail_path":    data.get("thumbnail_path"),
            "preview_path":      data.get("preview_path"),
            "mime_type":         data.get("mime_type", ""),
            "status":            data.get("status", ""),
            "asset_metadata":    data.get("asset_metadata", {}),
            "completeness_score": data.get("completeness_score", 0),
            "ai_summary":        data.get("ai_summary"),
            "perceptual_hash":   data.get("perceptual_hash"),
        })

    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return results[:limit]