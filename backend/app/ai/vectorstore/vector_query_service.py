# # performs semantic similarity retrieval

# from app.ai.vectorstore.vector_collection_service import (
#     VectorCollectionService
# )

# class VectorQueryService:

#     @staticmethod
#     def semantic_search(
#         query_embedding:list,
#         limit: int = 5
#     ):
        
#         collection = VectorCollectionService.get_collection()

#         results = collection.query(
#             query_embeddings=[query_embedding],
#             n_results= limit
#         )

#         return results
# vector_query_service.py
# Performs semantic similarity retrieval from ChromaDB.
#
# Returns documents + metadata so callers get full asset context,
# not just IDs. Supports optional where-filters for faceted search
# (e.g. only approved assets, specific domain/audience).

from app.ai.vectorstore.vector_collection_service import VectorCollectionService


class VectorQueryService:

    @staticmethod
    def semantic_search(
        query_embedding: list,
        limit: int = 5,
        where: dict | None = None,
    ) -> dict:
        """
        Retrieves the top-k most similar assets from ChromaDB.

        Args:
            query_embedding: Vector from generate_embedding(query_text)
            limit:           Number of results to return (default 5)
            where:           Optional ChromaDB metadata filter dict.
                             Only supports flat equality / $and / $or.

                             Examples:
                               {"status": "approved"}
                               {"$and": [{"status": "approved"},
                                         {"domain": "ai_services"}]}

        Returns:
            Raw ChromaDB result dict:
            {
                "ids":        [["uuid1", "uuid2", ...]],
                "distances":  [[0.21, 0.34, ...]],   # lower = more similar
                "documents":  [["semantic doc text", ...]],
                "metadatas":  [[{flat metadata dict}, ...]],
            }

        Note:
            distances are L2 by default in Chroma (lower = closer).
            SemanticSearchService normalises these into a 0-1 score.
        """
        collection = VectorCollectionService.get_collection()

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results":        limit,
            "include":          ["documents", "metadatas", "distances"],
        }

        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)

        return results

    @staticmethod
    def search_approved_only(
        query_embedding: list,
        limit: int = 5,
        extra_filters: dict | None = None,
    ) -> dict:
        """
        Convenience wrapper: always filters to approved assets only.
        Optionally stack additional filters (domain, audience, etc.).

        Args:
            query_embedding: Vector from generate_embedding()
            limit:           Number of results
            extra_filters:   Additional flat key=value filters to AND with status=approved.
                             Example: {"domain": "ai_services", "audience": "enterprise"}

        Returns:
            Same structure as semantic_search().
        """
        if extra_filters:
            where = {
                "$and": [
                    {"status": "approved"},
                    *[{k: v} for k, v in extra_filters.items()]
                ]
            }
        else:
            where = {"status": "approved"}

        return VectorQueryService.semantic_search(
            query_embedding=query_embedding,
            limit=limit,
            where=where,
        )