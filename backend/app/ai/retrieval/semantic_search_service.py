# from uuid import UUID

from sqlalchemy.orm import Session
from app.models.asset.asset_model import Asset

from app.ai.pipelines.retrieval_pipeline import (
    RetrievalPipeline
)


class SemanticSearchService:

    @staticmethod
    def search(
        db: Session,
        query:str,
        limit: int = 5,
        approved_only: bool = True
    ):
        
        # VECTOR SEARCH
        results = (
            RetrievalPipeline.semantic_search(
            query=query,
            limit=limit
            )
        )

        print("\nVECTOR RESULT")
        print(results)

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not ids:
            return []
        
        # documents = results.get("documents", [[]])[0]
        # metadatas = results.get("metadatas", [[]])[0]


        # FETCH ASSETS FROM POSTGRES
        uuid_ids = [str(asset_id) for asset_id in ids]
        assets = (
            db.query(Asset).filter(Asset.id.in_(uuid_ids)).all()
        )

        # APPROVED FILTER
        if approved_only:
            assets = [
                asset
                for asset in assets
                if asset.status == "approved"
            ]

        # MAP ASSETS BY ID
        asset_map = {
            str(asset.id): asset
            for asset in assets
        }


        formatted_results = []

        for idx, asset_id in enumerate(ids):

            asset = asset_map.get(asset_id)

            if not asset: continue


            similarity_score = round(
                max(0, 1-distances[idx]),
                4
            )

            formatted_results.append({

                # VECTOR DATA
                "score": similarity_score,
                
                
                # POSTGRES DATA
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

                "asset_metadata": (
                    asset.asset_metadata
                ),
            })

        return formatted_results