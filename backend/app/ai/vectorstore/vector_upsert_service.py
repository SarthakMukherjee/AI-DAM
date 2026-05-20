# Stores semantic embeddings

from app.ai.vectorstore.vector_collection_service import (
    VectorCollectionService
)

class VectorUpsertService:

    @staticmethod
    def upsert_embedding(
        asset_id: str,
        embedding: list,
        document: str,
        metadata: dict
    ):
        
        collection = VectorCollectionService.get_collection()

        collection.upsert(
            ids=[asset_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )

        return True

