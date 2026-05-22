# # semantic_search_service.py
# # Orchestrates the full semantic search pipeline for DAM assets.
# #
# # Two responsibilities:
# #   1. INDEXING  — embed an asset and store it in ChromaDB
# #   2. SEARCHING — embed a query and return ranked, formatted results
# #
# # This is the only file your API routes / asset_service.py should call.

# from app.ai.embeddings.embedding_utils import embed_asset, generate_embedding
# from app.ai.vectorstore.vector_upsert_service import VectorUpsertService
# from app.ai.vectorstore.vector_query_service import VectorQueryService


# # ---------------------------------------------------------------------------
# # Similarity scoring
# # ---------------------------------------------------------------------------

# def _distance_to_score(distance: float) -> float:
#     """
#     Converts ChromaDB L2 distance → 0-1 relevance score.
#     L2 distance of 0 = identical → score 1.0
#     We cap at distance=2.0 (anything beyond is not relevant).
#     """
#     score = max(0.0, 1.0 - (distance / 2.0))
#     return round(score, 4)


# # ---------------------------------------------------------------------------
# # Result formatting
# # ---------------------------------------------------------------------------

# def _format_results(raw: dict) -> list[dict]:
#     """
#     Converts raw ChromaDB query output into a clean list of result dicts.

#     Each result:
#     {
#         "asset_id":    str,
#         "score":       float,   # 0-1, higher = more relevant
#         "asset_name":  str,
#         "asset_type":  str,
#         "domain":      str,
#         "use_case":    str,
#         "audience":    str,
#         "funnel_stage": str,
#         "tone":        str,
#         "ai_tags":     list[str],
#         "image_caption": str,
#         "document":    str,     # full semantic text that was embedded
#     }
#     """
#     ids        = raw.get("ids", [[]])[0]
#     distances  = raw.get("distances", [[]])[0]
#     metadatas  = raw.get("metadatas", [[]])[0]
#     documents  = raw.get("documents", [[]])[0]

#     results = []
#     for asset_id, distance, meta, doc in zip(ids, distances, metadatas, documents):
#         results.append({
#             "asset_id":     asset_id,
#             "score":        _distance_to_score(distance),

#             # flat metadata fields (mirrors _flatten_metadata output)
#             "asset_name":   meta.get("asset_name", ""),
#             "asset_type":   meta.get("asset_type", ""),
#             "domain":       meta.get("domain", ""),
#             "use_case":     meta.get("use_case", ""),
#             "audience":     meta.get("audience", ""),
#             "funnel_stage": meta.get("funnel_stage", ""),
#             "tone":         meta.get("tone", ""),
#             "owner":        meta.get("owner", ""),
#             "ai_tags":      [t.strip() for t in meta.get("ai_tags", "").split(",") if t.strip()],
#             "image_caption": meta.get("image_caption", ""),
#             "status":       meta.get("status", ""),

#             "document":     doc,  # full semantic text — useful for debugging
#         })

#     return results


# # ---------------------------------------------------------------------------
# # SemanticSearchService
# # ---------------------------------------------------------------------------

# class SemanticSearchService:

#     # -----------------------------------------------------------------------
#     # INDEXING
#     # -----------------------------------------------------------------------

#     @staticmethod
#     def index_asset(
#         asset_id: str,
#         asset: dict,
#         status: str = "approved",
#     ) -> bool:
#         """
#         Embeds an asset and stores it in ChromaDB.
#         Call this after an asset is uploaded + AI-enriched.

#         Args:
#             asset_id:  DB UUID of the asset
#             asset:     Full asset dict with mandatory/business/content/ai_enrichment
#             status:    Lifecycle status ("draft" | "approved" | "archived")

#         Returns:
#             True on success.

#         Usage:
#             SemanticSearchService.index_asset(
#                 asset_id=str(asset.id),
#                 asset=asset.metadata,       # the AssetMetadataSchema dict
#                 status=asset.status,
#             )
#         """
#         document, embedding = embed_asset(asset)

#         VectorUpsertService.upsert_embedding(
#             asset_id=asset_id,
#             embedding=embedding,
#             document=document,
#             asset=asset,
#             status=status,
#         )

#         return True

#     @staticmethod
#     def reindex_asset(
#         asset_id: str,
#         asset: dict,
#         status: str = "approved",
#     ) -> bool:
#         """
#         Re-embeds and overwrites an existing asset vector.
#         Call this when metadata or AI enrichment is updated.
#         ChromaDB upsert() is idempotent — same ID = overwrite.
#         """
#         return SemanticSearchService.index_asset(asset_id, asset, status)

#     # -----------------------------------------------------------------------
#     # SEARCHING
#     # -----------------------------------------------------------------------

#     @staticmethod
#     def search(
#         query: str,
#         limit: int = 10,
#         approved_only: bool = True,
#         filters: dict | None = None,
#     ) -> list[dict]:
#         """
#         Main semantic search entry point.

#         Args:
#             query:          Natural language search string.
#                             e.g. "AI landing page banner for enterprise clients"
#             limit:          Max results to return (default 10)
#             approved_only:  If True, only return approved assets (recommended)
#             filters:        Optional metadata filters to narrow results.
#                             Keys must match flat metadata fields:
#                               domain, use_case, audience, funnel_stage, asset_type, tone
#                             Example:
#                               {"domain": "ai_services", "audience": "enterprise"}

#         Returns:
#             List of result dicts, sorted by relevance score descending.
#             See _format_results() for the shape of each dict.

#         Example:
#             results = SemanticSearchService.search(
#                 query="Homepage AI banner for enterprise audience",
#                 approved_only=True,
#                 filters={"asset_type": "banner"},
#             )
#         """
#         # 1. Embed the query using the same model as asset indexing
#         query_embedding = generate_embedding(query)

#         # 2. Retrieve from ChromaDB
#         if approved_only:
#             raw = VectorQueryService.search_approved_only(
#                 query_embedding=query_embedding,
#                 limit=limit,
#                 extra_filters=filters,
#             )
#         else:
#             where = None
#             if filters:
#                 if len(filters) == 1:
#                     where = filters
#                 else:
#                     where = {"$and": [{k: v} for k, v in filters.items()]}

#             raw = VectorQueryService.semantic_search(
#                 query_embedding=query_embedding,
#                 limit=limit,
#                 where=where,
#             )

#         # 3. Format and return
#         return _format_results(raw)

#     @staticmethod
#     def search_by_asset_type(
#         query: str,
#         asset_type: str,
#         limit: int = 10,
#     ) -> list[dict]:
#         """Shortcut: search within a specific asset type (image, video, banner…)."""
#         return SemanticSearchService.search(
#             query=query,
#             limit=limit,
#             approved_only=True,
#             filters={"asset_type": asset_type},
#         )

#     @staticmethod
#     def search_by_audience(
#         query: str,
#         audience: str,
#         limit: int = 10,
#     ) -> list[dict]:
#         """Shortcut: search assets targeting a specific audience."""
#         return SemanticSearchService.search(
#             query=query,
#             limit=limit,
#             approved_only=True,
#             filters={"audience": audience},
#         )
# semantic_search_service.py
# Orchestrates the full semantic search pipeline for DAM assets.
#
# INDEXING:  embed asset_metadata and store in ChromaDB
# SEARCHING: embed a query and return ranked, formatted results
# =====================================================================
# from app.ai.embeddings.embedding_utils import embed_asset, generate_embedding
# from app.ai.vectorstore.vector_upsert_service import VectorUpsertService
# from app.ai.vectorstore.vector_query_service import VectorQueryService


# def _distance_to_score(distance: float) -> float:
#     """L2 distance → 0-1 relevance score. Lower distance = higher score."""
#     score = max(0.0, 1.0 - (distance / 2.0))
#     return round(score, 4)


# def _format_results(raw: dict) -> list[dict]:
#     ids        = raw.get("ids", [[]])[0]
#     distances  = raw.get("distances", [[]])[0]
#     metadatas  = raw.get("metadatas", [[]])[0]
#     documents  = raw.get("documents", [[]])[0]

#     results = []
#     for asset_id, distance, meta, doc in zip(ids, distances, metadatas, documents):
#         results.append({
#             "asset_id":      asset_id,
#             "score":         _distance_to_score(distance),
#             "asset_name":    meta.get("asset_name", ""),
#             "asset_type":    meta.get("asset_type", ""),
#             "domain":        meta.get("domain", ""),
#             "use_case":      meta.get("use_case", ""),
#             "audience":      meta.get("audience", ""),
#             "funnel_stage":  meta.get("funnel_stage", ""),
#             "tone":          meta.get("tone", ""),
#             "owner":         meta.get("owner", ""),
#             "status":        meta.get("status", ""),
#             "ai_tags":       [t.strip() for t in meta.get("ai_tags", "").split(",") if t.strip()],
#             "image_caption": meta.get("image_caption", ""),
#             "document":      doc,
#         })

#     return results


# class SemanticSearchService:

#     # -----------------------------------------------------------------------
#     # INDEXING
#     # -----------------------------------------------------------------------

#     @staticmethod
#     def index_asset(
#         asset_id: str,
#         asset_metadata: dict,
#         status: str = "approved",
#     ) -> bool:
#         """
#         Embeds asset_metadata and stores it in ChromaDB.
#         Call this after upload + AI enrichment completes.

#         Args:
#             asset_id:       DB UUID of the asset
#             asset_metadata: asset.asset_metadata from PostgreSQL
#                             (the dict with mandatory/business/content/ai_enrichment)
#             status:         "draft" | "approved" | "archived"
#         """
#         document, embedding = embed_asset(asset_metadata)

#         VectorUpsertService.upsert_embedding(
#             asset_id=asset_id,
#             embedding=embedding,
#             document=document,
#             asset=asset_metadata,
#             status=status,
#         )

#         return True

#     @staticmethod
#     def reindex_asset(
#         asset_id: str,
#         asset_metadata: dict,
#         status: str = "approved",
#     ) -> bool:
#         """
#         Re-embeds and overwrites an existing asset vector.
#         Call when metadata is updated or status changes.
#         """
#         return SemanticSearchService.index_asset(asset_id, asset_metadata, status)

#     # -----------------------------------------------------------------------
#     # SEARCHING
#     # -----------------------------------------------------------------------

#     @staticmethod
#     def search(
#         query: str,
#         limit: int = 10,
#         approved_only: bool = True,
#         filters: dict | None = None,
#     ) -> list[dict]:
#         """
#         Natural language semantic search.

#         Args:
#             query:         e.g. "AI landing page banner for enterprise clients"
#             limit:         max results
#             approved_only: only return approved assets (recommended)
#             filters:       flat metadata filters
#                            e.g. {"asset_type": "banner", "audience": "enterprise"}
#         """
#         query_embedding = generate_embedding(query)

#         if approved_only:
#             raw = VectorQueryService.search_approved_only(
#                 query_embedding=query_embedding,
#                 limit=limit,
#                 extra_filters=filters,
#             )
#         else:
#             where = None
#             if filters:
#                 where = filters if len(filters) == 1 else {
#                     "$and": [{k: v} for k, v in filters.items()]
#                 }

#             raw = VectorQueryService.semantic_search(
#                 query_embedding=query_embedding,
#                 limit=limit,
#                 where=where,
#             )

#         return _format_results(raw)

#     @staticmethod
#     def search_by_asset_type(query: str, asset_type: str, limit: int = 10) -> list[dict]:
#         return SemanticSearchService.search(query, limit, True, {"asset_type": asset_type})

#     @staticmethod
#     def search_by_audience(query: str, audience: str, limit: int = 10) -> list[dict]:
#         return SemanticSearchService.search(query, limit, True, {"audience": audience})

# =====================================================================

from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

from app.ai.embeddings.embedding_utils import (
    embed_asset,
    generate_embedding,
)

from app.ai.vectorstore.vector_upsert_service import (
    VectorUpsertService
)

from app.ai.vectorstore.vector_query_service import (
    VectorQueryService
)


# =========================================================
# UTILITY
# =========================================================

def _distance_to_score(
    distance: float
) -> float:
    """
    Converts vector distance into similarity score.

    Lower distance = Higher similarity
    """

    score = max(
        0.0,
        1.0 - (distance / 2.0)
    )

    return round(score, 4)


# =========================================================
# SEMANTIC SEARCH SERVICE
# =========================================================

class SemanticSearchService:

    # =====================================================
    # INDEX ASSET
    # =====================================================

    @staticmethod
    def index_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved",
    ) -> bool:
        """
        Generates semantic document + embedding
        and stores them in ChromaDB.
        """

        # ---------------------------------------------
        # GENERATE SEMANTIC DOCUMENT + EMBEDDING
        # ---------------------------------------------

        document, embedding = embed_asset(
            asset_metadata
        )

        # ---------------------------------------------
        # STORE IN VECTOR DB
        # ---------------------------------------------

        VectorUpsertService.upsert_embedding(
            asset_id=asset_id,
            embedding=embedding,
            document=document,
            asset=asset_metadata,
            status=status,
        )

        return True

    # =====================================================
    # REINDEX ASSET
    # =====================================================

    @staticmethod
    def reindex_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved",
    ) -> bool:
        """
        Rebuilds embedding for existing asset.
        """

        return SemanticSearchService.index_asset(
            asset_id=asset_id,
            asset_metadata=asset_metadata,
            status=status,
        )

    # =====================================================
    # SEMANTIC SEARCH
    # =====================================================

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 5,
        approved_only: bool = True,
        filters: dict | None = None,
    ) -> list[dict]:

        # -------------------------------------------------
        # STEP 1
        # QUERY → EMBEDDING
        # -------------------------------------------------

        query_embedding = generate_embedding(
            query
        )

        # -------------------------------------------------
        # STEP 2
        # CHROMADB VECTOR SEARCH
        # -------------------------------------------------

        if approved_only:

            raw_results = (
                VectorQueryService
                .search_approved_only(
                    query_embedding=query_embedding,
                    limit=limit,
                    extra_filters=filters,
                )
            )

        else:

            where = None

            if filters:

                if len(filters) == 1:

                    where = filters

                else:

                    where = {
                        "$and": [
                            {k: v}
                            for k, v in filters.items()
                        ]
                    }

            raw_results = (
                VectorQueryService
                .semantic_search(
                    query_embedding=query_embedding,
                    limit=limit,
                    where=where,
                )
            )

        # -------------------------------------------------
        # STEP 3
        # EXTRACT MATCHED ASSET IDS
        # -------------------------------------------------

        asset_ids = (
            raw_results.get("ids", [[]])[0]
        )

        distances = (
            raw_results.get("distances", [[]])[0]
        )

        if not asset_ids:
            return []

        # -------------------------------------------------
        # STEP 4
        # FETCH ASSETS FROM POSTGRESQL
        # -------------------------------------------------

        assets = (
            db.query(Asset)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )

        # -------------------------------------------------
        # APPROVED FILTER
        # -------------------------------------------------

        if approved_only:

            assets = [

                asset

                for asset in assets

                if asset.status == "approved"
            ]

        # -------------------------------------------------
        # CREATE ASSET MAP
        # -------------------------------------------------

        asset_map = {

            str(asset.id): asset

            for asset in assets
        }

        # -------------------------------------------------
        # STEP 5
        # MERGE VECTOR SCORES + POSTGRES DATA
        # -------------------------------------------------

        formatted_results = []

        for idx, asset_id in enumerate(asset_ids):

            asset = asset_map.get(asset_id)

            if not asset:
                continue

            similarity_score = (
                _distance_to_score(
                    distances[idx]
                )
                if distances
                else None
            )

            formatted_results.append({

                # -----------------------------------------
                # VECTOR SEARCH SCORE
                # -----------------------------------------

                "similarity_score": (
                    similarity_score
                ),

                # -----------------------------------------
                # POSTGRES ASSET DATA
                # -----------------------------------------

                "asset_id": str(asset.id),

                "original_filename": (
                    asset.original_filename
                ),

                "storage_path": (
                    asset.storage_path
                ),

                "thumbnail_path": (
                    asset.thumbnail_path
                ),

                "preview_path": (
                    asset.preview_path
                ),

                "mime_type": (
                    asset.mime_type
                ),

                "status": (
                    asset.status
                ),

                "created_at": (
                    asset.created_at
                ),

                "asset_metadata": (
                    asset.asset_metadata
                ),
            })

        # -------------------------------------------------
        # STEP 6
        # FRONTEND READY RESPONSE
        # -------------------------------------------------

        return formatted_results

    # =====================================================
    # FILTERED SEARCH HELPERS
    # =====================================================

    @staticmethod
    def search_by_asset_type(
        db: Session,
        query: str,
        asset_type: str,
        limit: int = 10,
    ):

        return SemanticSearchService.search(
            db=db,
            query=query,
            limit=limit,
            approved_only=True,
            filters={
                "asset_type": asset_type
            },
        )

    @staticmethod
    def search_by_audience(
        db: Session,
        query: str,
        audience: str,
        limit: int = 10,
    ):

        return SemanticSearchService.search(
            db=db,
            query=query,
            limit=limit,
            approved_only=True,
            filters={
                "audience": audience
            },
        )