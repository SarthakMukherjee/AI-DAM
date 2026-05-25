from app.ai.embeddings.embedding_service import (
    EmbeddingService
)

from app.ai.vectorstore.vector_query_service import (
    VectorQueryService
)


class RetrievalPipeline:

    def semantic_search(
            query: str,
            limit: int = 5,
            where: dict | None = None
    ):
        
        # Query Embedding
        query_embedding = (
            EmbeddingService.generate_embeddings(
            query
            )
        )

        # Vector Search
        results = (
            VectorQueryService.semantic_search(
            query_embedding,
            limit=limit,
            where=where
        )
        )

        return results
        


