# # from uuid import UUID

# from sqlalchemy.orm import Session
# from app.models.asset.asset_model import Asset

# from app.ai.pipelines.retrieval_pipeline import (
#     RetrievalPipeline
# )

# from app.ai.embeddings.embedding_utils import(
#     embed_asset,
#     generate_embedding
# )

# from app.ai.vectorstore.vector_upsert_service import (
#     VectorUpsertService
# )

# from app.ai.vectorstore.vector_query_service import (
#     VectorQueryService
# )

# MINIMUM_SIMILARITY_SCORE = 0.45

# # DISTANCE -> SCORE
# def _distance_to_score(
#         distance: float
# ) -> float:
    
#     score = max(
#         0.0,
#         1.0-(distance /  2.0)
#     )

#     return round(score, 4)

# def _fetch_assets_by_ids(
#         asset_ids: list[str],
#         db: Session
# ):
#     assets = (
#         db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
#     )

#     return {
#         str(asset.id): asset for asset in assets
#     }


# def _format_results(
#     raw: dict,
#     db: Session,
#     limit: int
# ):

#     ids = raw.get("ids", [[]])[0]
#     distances = raw.get("distances", [[]])[0]

#     if not ids:
#         return []

#     # -------------------------------------------------
#     # FETCH REAL ASSETS
#     # -------------------------------------------------

#     asset_map = _fetch_assets_by_ids(
#         ids,
#         db
#     )

#     formatted_results = []

#     # -------------------------------------------------
#     # BUILD RESULTS
#     # -------------------------------------------------

#     for asset_id, distance in zip(ids, distances):

#         asset = asset_map.get(asset_id)

#         if not asset:
#             continue

#         # ---------------------------------------------
#         # DISTANCE → SCORE
#         # ---------------------------------------------

#         score = _distance_to_score(distance)

#         # ---------------------------------------------
#         # THRESHOLD FILTERING
#         # ---------------------------------------------

#         if score < MINIMUM_SIMILARITY_SCORE:
#             continue

#         # ---------------------------------------------
#         # BUILD RESPONSE
#         # ---------------------------------------------

#         formatted_results.append({

#             "asset_id": str(asset.id),

#             "score": score,

#             "original_filename":
#                 asset.original_filename,

#             "storage_path":
#                 asset.storage_path,

#             "thumbnail_path":
#                 asset.thumbnail_path,

#             "preview_path":
#                 asset.preview_path,

#             "mime_type":
#                 asset.mime_type,

#             "status":
#                 asset.status,

#             "asset_metadata":
#                 asset.asset_metadata or {}
#         })

#     # -------------------------------------------------
#     # SORT BEST → WORST
#     # -------------------------------------------------

#     formatted_results.sort(
#         key=lambda x: x["score"],
#         reverse=True
#     )

#     # -------------------------------------------------
#     # FINAL LIMIT
#     # -------------------------------------------------

#     return formatted_results[:limit]


# class SemanticSearchService:

#     @staticmethod
#     def index_asset(
#         asset_id: str,
#         asset_metadata: dict,
#         status: str = "approved"
#     ):
#         document, embedding = embed_asset(asset_metadata)

#         VectorUpsertService.upsert_embedding(
#             asset_id=asset_id,
#             embedding=embedding,
#             document=document,
#             asset=asset_metadata,
#             status=status
#         )

#         return True

#     @staticmethod
#     def reindex_asset(
#         asset_id: str,
#         asset_metadata: dict,
#         status: str = "approved"
#     ):

#         return SemanticSearchService.index_asset(
#             asset_id,
#             asset_metadata,
#             status
#         )
    

#     @staticmethod
#     def search(
#         db: Session,
#         query:str,
#         limit: int = 10,
#         approved_only: bool = True,
#         filters: dict | None = None
#     ):
        
#         query_embedding = generate_embedding(query)
        
#         if approved_only:
#             raw = (
#                 VectorQueryService.search_approved_only(
#                 query_embedding=query_embedding,
#                 limit=limit,
#                 extra_filters=filters
#                 )
#             )
#         else:
#             where = None
#             if filters:
#                 where = {
#                     "$and": [
#                         {k, v}
#                         for k, v in filters.items()
#                     ]
#                 }

#             raw = (
#                 VectorQueryService.semantic_search(
#                     query_embedding=query_embedding,
#                     limit=limit
#                     where=where
#                 )
#             )

#         # VECTOR SEARCH
#         results = (
#             RetrievalPipeline.semantic_search(
#             query=query,
#             limit=limit
#             )
#         )

#         print("\nVECTOR RESULT")
#         print(results)

#         ids = results.get("ids", [[]])[0]
#         distances = results.get("distances", [[]])[0]

#         if not ids:
#             return []
        
#         # documents = results.get("documents", [[]])[0]
#         # metadatas = results.get("metadatas", [[]])[0]


#         # FETCH ASSETS FROM POSTGRES
#         uuid_ids = [str(asset_id) for asset_id in ids]
#         assets = (
#             db.query(Asset).filter(Asset.id.in_(uuid_ids)).all()
#         )

#         # APPROVED FILTER
#         if approved_only:
#             assets = [
#                 asset
#                 for asset in assets
#                 if asset.status == "approved"
#             ]

#         # MAP ASSETS BY ID
#         asset_map = {
#             str(asset.id): asset
#             for asset in assets
#         }


#         formatted_results = []

#         for idx, asset_id in enumerate(ids):

#             asset = asset_map.get(asset_id)

#             if not asset: continue


#             similarity_score = round(
#                 max(0, 1-distances[idx]),
#                 4
#             )

#             formatted_results.append({

#                 # VECTOR DATA
#                 "score": similarity_score,
                
                
#                 # POSTGRES DATA
#                 "asset_id": str(asset.id),

#                 "original_filename": (
#                     asset.original_filename
#                 ),

#                 "storage_path": (
#                     asset.storage_path
#                 ),

#                 "thumbnail_path": (
#                     asset.thumbnail_path
#                 ),

#                 "preview_path": (
#                     asset.preview_path
#                 ),

#                 "mime_type": (
#                     asset.mime_type
#                 ),

#                 "status": (
#                     asset.status
#                 ),

#                 "asset_metadata": (
#                     asset.asset_metadata
#                 ),
#             })

#         return formatted_results


from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

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
MAXIMUM_RETURNED_ASSETS = 3

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
    limit: int
):

    ids = raw.get("ids", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    if not ids:
        return []

    # -------------------------------------------------
    # FETCH REAL ASSETS
    # -------------------------------------------------

    asset_map = _fetch_assets_by_ids(
        ids,
        db
    )

    formatted_results = []

    # -------------------------------------------------
    # BUILD RESULTS
    # -------------------------------------------------

    for asset_id, distance in zip(ids, distances):

        asset = asset_map.get(asset_id)

        if not asset:
            continue

        # ---------------------------------------------
        # DISTANCE → SCORE
        # ---------------------------------------------

        score = _distance_to_score(distance)

        # ---------------------------------------------
        # THRESHOLD FILTERING
        # ---------------------------------------------

        if score < MINIMUM_SIMILARITY_SCORE:
            continue

        # ---------------------------------------------
        # BUILD RESPONSE
        # ---------------------------------------------

        formatted_results.append({

            "asset_id": str(asset.id),

            "score": score,

            "original_filename":
                asset.original_filename,

            "storage_path":
                asset.storage_path,

            "thumbnail_path":
                asset.thumbnail_path,

            "preview_path":
                asset.preview_path,

            "mime_type":
                asset.mime_type,

            "status":
                asset.status,

            "asset_metadata":
                asset.asset_metadata or {}
        })

    # -------------------------------------------------
    # SORT BEST → WORST
    # -------------------------------------------------

    formatted_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # -------------------------------------------------
    # FINAL LIMIT
    # -------------------------------------------------

    return formatted_results[:MAXIMUM_RETURNED_ASSETS]


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
        filters: dict | None = None
    ):

        # ---------------------------------------------
        # QUERY → EMBEDDING
        # ---------------------------------------------

        query_embedding = generate_embedding(
            query
        )

        # ---------------------------------------------
        # APPROVED FILTERS
        # ---------------------------------------------

        if approved_only:

            raw = (
                VectorQueryService.search_approved_only(
                    query_embedding=query_embedding,
                    limit=limit,
                    extra_filters=filters
                )
            )

        else:

            where = None

            if filters:

                where = {
                    "$and": [
                        {k: v}
                        for k, v in filters.items()
                    ]
                }

            raw = (
                VectorQueryService.semantic_search(
                    query_embedding=query_embedding,
                    limit=limit,
                    where=where
                )
            )

        # ---------------------------------------------
        # FORMAT RESULTS
        # ---------------------------------------------

        return _format_results(
            raw=raw,
            db=db,
            limit=limit
        )