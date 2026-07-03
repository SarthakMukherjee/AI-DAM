from app.ai.vectorstore.vector_collection_service import ( VectorCollectionService
)

class VectorDeleteService:
    """
    Handles deletion of the asset vectors in chromdb.

    Used whenever an asset is permanently removed from the database.
    """

    @staticmethod
    def delete_asset(
        asset_id:str
    )-> bool:
        
        collection=(
            VectorCollectionService.get_collection()
        )

        collection.delete(
            ids=[asset_id]
        )

        return True