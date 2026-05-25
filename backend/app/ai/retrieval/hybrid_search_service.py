# # # hybrid_search_service.py
# # # Combines keyword search (PostgreSQL) + semantic search (ChromaDB)
# # # into a single re-ranked result list.
# # #
# # # Scoring:
# # #   hybrid_score = (semantic_score * 0.6) + (keyword_score * 0.4)
# # #
# # # Semantic gets higher weight — it understands context and meaning.
# # # Keyword gets lower weight — it rewards exact matches as a precision boost.
# # #
# # # Deduplication: if an asset appears in both results,
# # # scores are combined. If only in one, the missing score is 0.

# # from sqlalchemy.orm import Session

# # from app.ai.embeddings.semantic_search_service import SemanticSearchService
# # from app.ai.embeddings.keyword_search_service import KeywordSearchService


# # # Weights — must sum to 1.0
# # SEMANTIC_WEIGHT = 0.6
# # KEYWORD_WEIGHT  = 0.4


# # class HybridSearchService:

# #     @staticmethod
# #     def search(
# #         query: str,
# #         db: Session,
# #         limit: int = 10,
# #         approved_only: bool = True,
# #         filters: dict | None = None,
# #     ) -> list[dict]:
# #         """
# #         Hybrid search: keyword (PostgreSQL) + semantic (ChromaDB),
# #         merged and re-ranked by weighted combined score.

# #         Args:
# #             query:         Natural language or keyword query
# #                            e.g. "enterprise AI banner homepage"
# #             db:            SQLAlchemy session (for keyword search)
# #             limit:         Final number of results to return
# #             approved_only: Only return approved assets
# #             filters:       Optional metadata filters for semantic search
# #                            e.g. {"asset_type": "banner"}

# #         Returns:
# #             List of result dicts sorted by hybrid_score descending.
# #             Each result includes:
# #                 asset_id, hybrid_score, semantic_score, keyword_score,
# #                 asset_name, asset_type, domain, use_case, audience,
# #                 funnel_stage, tone, owner, status, ai_tags, image_caption
# #         """

# #         # Fetch more than limit from each source before merging
# #         fetch_limit = limit * 3

# #         # ------------------------------------------------
# #         # 1. KEYWORD SEARCH — PostgreSQL
# #         # ------------------------------------------------
# #         keyword_results = KeywordSearchService.search(
# #             query=query,
# #             db=db,
# #             limit=fetch_limit,
# #             approved_only=approved_only,
# #         )

# #         # ------------------------------------------------
# #         # 2. SEMANTIC SEARCH — ChromaDB
# #         # ------------------------------------------------
# #         semantic_results = SemanticSearchService.search(
# #             query=query,
# #             limit=fetch_limit,
# #             approved_only=approved_only,
# #             filters=filters,
# #         )

# #         # ------------------------------------------------
# #         # 3. MERGE + RE-RANK
# #         # ------------------------------------------------
# #         merged = _merge_and_rank(
# #             keyword_results=keyword_results,
# #             semantic_results=semantic_results,
# #             limit=limit,
# #         )

# #         return merged


# # # ---------------------------------------------------------------------------
# # # Merge + re-rank logic
# # # ---------------------------------------------------------------------------

# # def _merge_and_rank(
# #     keyword_results: list[dict],
# #     semantic_results: list[dict],
# #     limit: int,
# # ) -> list[dict]:
# #     """
# #     Merges two result lists into one re-ranked list.

# #     - Builds a map of asset_id → scores from both sources
# #     - If asset appears in both: combines scores with weights
# #     - If asset appears in only one: missing score = 0
# #     - Sorts by hybrid_score descending
# #     - Returns top `limit` results
# #     """

# #     # Map: asset_id → result dict with both scores
# #     merged: dict[str, dict] = {}

# #     # Index keyword results
# #     for r in keyword_results:
# #         asset_id = r["asset_id"]
# #         merged[asset_id] = {
# #             **r,
# #             "keyword_score":  r.get("keyword_score", 0.0),
# #             "semantic_score": 0.0,
# #         }

# #     # Merge semantic results
# #     for r in semantic_results:
# #         asset_id = r["asset_id"]
# #         if asset_id in merged:
# #             # Asset found in both — combine
# #             merged[asset_id]["semantic_score"] = r.get("score", 0.0)
# #             # Fill any missing fields from semantic result
# #             for field in ["asset_name", "asset_type", "domain", "use_case",
# #                           "audience", "funnel_stage", "tone", "owner",
# #                           "status", "ai_tags", "image_caption"]:
# #                 if not merged[asset_id].get(field):
# #                     merged[asset_id][field] = r.get(field, "")
# #         else:
# #             # Only in semantic results
# #             merged[asset_id] = {
# #                 **r,
# #                 "keyword_score":  0.0,
# #                 "semantic_score": r.get("score", 0.0),
# #             }

# #     # Compute hybrid score for every asset
# #     results = []
# #     for asset_id, data in merged.items():
# #         hybrid_score = round(
# #             (data["semantic_score"] * SEMANTIC_WEIGHT) +
# #             (data["keyword_score"]  * KEYWORD_WEIGHT),
# #             4
# #         )
# #         results.append({
# #             "asset_id":       asset_id,
# #             "hybrid_score":   hybrid_score,
# #             "semantic_score": round(data["semantic_score"], 4),
# #             "keyword_score":  round(data["keyword_score"], 4),
# #             "asset_name":     data.get("asset_name", ""),
# #             "asset_type":     data.get("asset_type", ""),
# #             "domain":         data.get("domain", ""),
# #             "use_case":       data.get("use_case", ""),
# #             "audience":       data.get("audience", ""),
# #             "funnel_stage":   data.get("funnel_stage", ""),
# #             "tone":           data.get("tone", ""),
# #             "owner":          data.get("owner", ""),
# #             "status":         data.get("status", ""),
# #             "ai_tags":        data.get("ai_tags", []),
# #             "image_caption":  data.get("image_caption", ""),
# #             "original_filename": data.get("original_filename", ""),
# #         })

# #     # Sort by hybrid_score descending
# #     results.sort(key=lambda x: x["hybrid_score"], reverse=True)

# #     return results[:limit]

# # hybrid_search_service.py
# # Combines keyword (PostgreSQL) + semantic (ChromaDB) search.
# # Results merged and re-ranked by weighted combined score.
# #
# # hybrid_score = semantic_score * 0.6 + keyword_score * 0.4

# from sqlalchemy.orm import Session

# from app.ai.embeddings.semantic_search_service import SemanticSearchService
# from app.ai.embeddings.keyword_search_service import KeywordSearchService

# SEMANTIC_WEIGHT = 0.6
# KEYWORD_WEIGHT  = 0.4


# class HybridSearchService:

#     @staticmethod
#     def search(
#         query: str,
#         db: Session,
#         limit: int = 10,
#         approved_only: bool = True,
#         filters: dict | None = None,
#     ) -> list[dict]:

#         fetch_limit = limit * 3

#         # 1. Keyword search — PostgreSQL
#         keyword_results = KeywordSearchService.search(
#             query=query,
#             db=db,
#             limit=fetch_limit,
#             approved_only=approved_only,
#         )

#         # 2. Semantic search — ChromaDB + PostgreSQL full data
#         semantic_results = SemanticSearchService.search(
#             query=query,
#             db=db,
#             limit=fetch_limit,
#             approved_only=approved_only,
#             filters=filters,
#         )

#         # 3. Merge + re-rank
#         return _merge_and_rank(keyword_results, semantic_results, limit)


# def _merge_and_rank(
#     keyword_results: list[dict],
#     semantic_results: list[dict],
#     limit: int,
# ) -> list[dict]:

#     merged: dict[str, dict] = {}

#     # Index keyword results
#     for r in keyword_results:
#         asset_id = r["asset_id"]
#         merged[asset_id] = {
#             **r,
#             "keyword_score":  r.get("keyword_score", 0.0),
#             "semantic_score": 0.0,
#         }

#     # Merge semantic results
#     for r in semantic_results:
#         asset_id = r["asset_id"]
#         if asset_id in merged:
#             merged[asset_id]["semantic_score"] = r.get("score", 0.0)
#         else:
#             merged[asset_id] = {
#                 **r,
#                 "keyword_score":  0.0,
#                 "semantic_score": r.get("score", 0.0),
#             }

#     # Compute hybrid score and build final list
#     results = []
#     for asset_id, data in merged.items():
#         hybrid_score = round(
#             (data["semantic_score"] * SEMANTIC_WEIGHT) +
#             (data["keyword_score"]  * KEYWORD_WEIGHT),
#             4
#         )
#         results.append({
#             "asset_id":          asset_id,
#             "hybrid_score":      hybrid_score,
#             "semantic_score":    round(data["semantic_score"], 4),
#             "keyword_score":     round(data["keyword_score"], 4),
#             "original_filename": data.get("original_filename", ""),
#             "storage_path":      data.get("storage_path", ""),
#             "thumbnail_path":    data.get("thumbnail_path"),
#             "preview_path":      data.get("preview_path"),
#             "mime_type":         data.get("mime_type", ""),
#             "status":            data.get("status", ""),
#             "asset_metadata":    data.get("asset_metadata", {}),
#         })

#     results.sort(key=lambda x: x["hybrid_score"], reverse=True)
#     return results[:limit]
# app/ai/retrieval/hybrid_search_service.py
# Combines keyword (PostgreSQL) + semantic (ChromaDB) search.
# Re-ranks by weighted combined score.
#
# hybrid_score = semantic_score * 0.6 + keyword_score * 0.4

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
    ) -> list[dict]:
        """
        Hybrid search: keyword + semantic, merged and re-ranked.

        Args:
            db:            SQLAlchemy session
            query:         User search string
            limit:         Final number of results
            approved_only: Only approved assets

        Returns:
            List of result dicts sorted by hybrid_score descending.
            Each result includes hybrid_score, semantic_score, keyword_score
            plus full asset data (same shape as semantic search results).
        """

        fetch_limit = limit * 3

        # 1. KEYWORD — PostgreSQL
        keyword_results = KeywordSearchService.search(
            db=db,
            query=query,
            limit=fetch_limit,
            approved_only=approved_only,
        )

        # 2. SEMANTIC — ChromaDB + PostgreSQL
        semantic_results = SemanticSearchService.search(
            db=db,
            query=query,
            limit=fetch_limit,
            approved_only=approved_only,
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
        })

    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return results[:limit]