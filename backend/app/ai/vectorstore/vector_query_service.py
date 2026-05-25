# performs semantic similarity retrieval
# from app.ai.vectorstore.vector_collection_service import (
#     VectorCollectionService
# )

# class VectorQueryService:

#     @staticmethod
#     def semantic_search(
#         query_embedding:list,
#         limit: int = 10,
#         where: dict | None = None
#     ):
        
#         collection = VectorCollectionService.get_collection()

#         results = collection.query(
#             query_embeddings=[query_embedding],
#             n_results= max(limit*3, 15),
#             where=where
#         )

#         return results
    
#     # APPROVED ONLY SEARCH
#     @staticmethod
#     def search_approved_only(
#         query_embedding:list,
#         limit: int = 10,
#         extra_filters: dict | None = None
#     ):
#         where_clause =  {
#             "status":"approved"
#         }

#         if extra_filters:
#             where_clause = {
#                 "$and": [
#                     {"status":"approved"},
#                     *[
#                         {k: v}
#                         for k, v in extra_filters.items()
#                     ]
#                 ]
#             }

#         return VectorQueryService.semantic_search(
#             query_embedding=query_embedding,
#             limit=limit,
#             where=where_clause
#         )
# ====================================================================

from app.ai.vectorstore.vector_collection_service import (
    VectorCollectionService
)


class VectorQueryService:

    # ---------------------------------------------------------
    # ENTERPRISE SEMANTIC SEARCH
    # ---------------------------------------------------------

    @staticmethod
    def semantic_search(
        query_embedding: list,
        limit: int = 10,
        where: dict | None = None
    ):

        collection = (
            VectorCollectionService.get_collection()
        )

        # -----------------------------------------------------
        # ENTERPRISE RETRIEVAL STRATEGY
        # -----------------------------------------------------
        #
        # NEVER retrieve only "limit".
        #
        # We retrieve a large candidate pool first,
        # then semantic_search_service.py:
        #
        # - filters weak matches
        # - ranks results
        # - returns best matches only
        #
        # This dramatically improves retrieval quality.
        #
        # -----------------------------------------------------

        retrieval_pool_size = max(
            limit * 10,
            50
        )

        results = collection.query(
            query_embeddings=[query_embedding],

            # LARGE retrieval pool
            n_results=retrieval_pool_size,

            where=where
        )

        return results

    # ---------------------------------------------------------
    # APPROVED ONLY SEARCH
    # ---------------------------------------------------------

    @staticmethod
    def search_approved_only(
        query_embedding: list,
        limit: int = 10,
        extra_filters: dict | None = None
    ):

        where_clause = {
            "status": "approved"
        }

        # -----------------------------------------------------
        # MERGE EXTRA FILTERS
        # -----------------------------------------------------

        if extra_filters:

            where_clause = {
                "$and": [
                    {"status": "approved"},
                    *[
                        {k: v}
                        for k, v in extra_filters.items()
                    ]
                ]
            }

        return VectorQueryService.semantic_search(
            query_embedding=query_embedding,
            limit=limit,
            where=where_clause
        )