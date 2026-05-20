# Manages Semantic collections.

from app.ai.vectorstore.chroma_service import ChromaService

COLLECTION_NAME = "dam_sematic_assets"

class VectorCollectionService:

    @staticmethod
    def get_collection():

        client = ChromaService.get_client()

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description": "Semantic DAM Asset Collection"
            }
        )

        return collection
