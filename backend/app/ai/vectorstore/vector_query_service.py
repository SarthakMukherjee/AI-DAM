# performs semantic similarity retrieval

from app.ai.vectorstore.vector_collection_service import (
    VectorCollectionService
)

class VectorQueryService:

    @staticmethod
    def semantic_search(
        query_embedding:list,
        limit: int = 5
    ):
        
        collection = VectorCollectionService.get_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results= limit
        )

        return results