from app.ai.embeddings.embedding_utils import (
    build_semantic_document
)

from app.ai.embeddings.embedding_service import (
    EmbeddingService
)

from app.ai.vectorstore.vector_upsert_service import (
    VectorUpsertService
)

class EmbeddingPipeline:

    def process_asset_embedding(
            asset:dict,
            status: str = "approved"
    ):
        
        # Asset ID
        asset_id = str(asset.get("id"))

        # Build Semantic Document
        semantic_document = (
            build_semantic_document(asset)
        )

        # Generate Embedding
        embedding = (
            EmbeddingService.generate_embeddings(
            semantic_document
        )
        )

        # # Prepare Vector Metadata
        # metadata = asset.get("asset_metadata", {})

        # mandatory = metadata.get("mandatory", {})
        
        # business = metadata.get("business", {})

        # vector_metadata = {
        #     "asset_type":
        #         mandatory.get(
        #             "asset_type",
        #             ""
        #         ),

        #         "owner":
        #             mandatory.get(
        #                 "owner",
        #                 ""
        #             ),

        #         "domain":
        #             business.get(
        #             "domain",
        #             ""
        #         ),

        #         "use_case":
        #             business.get(
        #             "use_case",
        #             ""
        #         ),

        #         "storage_path":
        #             asset.get(
        #                 "storage_path",
        #                 ""
        #         )
        # }
        

        # Store Inside CHROMADB
        VectorUpsertService.upsert_embedding(
            asset_id=asset["id"],
            embedding=embedding,
            document=semantic_document,
            asset=asset.get(
                "asset_metadata",
                {}
            ),
            status=status
        )

        return {
            "asset_id" : asset_id,
            "semantic_documents": semantic_document,
            "embedding_dimension": len(embedding),
            "vector_status":"stored"
        }