# # from fastapi import HTTPException

# # from sqlalchemy.orm import Session

# # from app.models.asset.asset_model import Asset

# # from app.services.storage.storage_service import StorageService
# # from app.services.storage.thumbnail_service import ThumbnailService
# # from app.services.storage.pdf_preview_service import PDFPreviewService
# # from app.services.storage.video_preview_service import VideoPreviewService

# # from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline

# # from app.utils.file_utils import (
# #     calculate_file_hash,
# #     detect_mime_type,
# #     validate_mime_type
# # )


# # class AssetService:

# #     def __init__(self):

# #         self.storage_service = StorageService()

# #         self.thumbnail_service = ThumbnailService()

# #         self.pdf_preview_service = PDFPreviewService()

# #         self.video_preview_service = VideoPreviewService()

# #         self.enrichment_pipeline = EnrichmentPipeline()

# #     async def upload_asset(
# #         self,
# #         file,
# #         db: Session,
# #         metadata: dict = None,
# #         status: str = "draft",
# #         parent_id: str = None
# #     ):

# #         # =====================================================
# #         # STEP 1 — SAVE TO TEMP
# #         # =====================================================

# #         filename, temp_path, content = (
# #             await self.storage_service.save_to_temp(file)
# #         )

# #         # =====================================================
# #         # STEP 2 — HASH GENERATION
# #         # =====================================================

# #         file_hash = calculate_file_hash(content)

# #         # =====================================================
# #         # STEP 3 — DUPLICATE CHECK
# #         # =====================================================

# #         existing_asset = (
# #             db.query(Asset)
# #             .filter(Asset.file_hash == file_hash)
# #             .first()
# #         )

# #         if existing_asset and not parent_id:

# #             self.storage_service.delete_temp_file(temp_path)

# #             raise HTTPException(
# #                 status_code=409,
# #                 detail="Duplicate asset already exists"
# #             )

# #         # =====================================================
# #         # STEP 4 — VALIDATION
# #         # =====================================================

# #         mime_type = detect_mime_type(temp_path)

# #         validate_mime_type(mime_type)

# #         # =====================================================
# #         # STEP 5 — MOVE TO ORIGINALS
# #         # =====================================================

# #         original_path = (
# #             self.storage_service.move_to_original(
# #                 temp_path,
# #                 filename
# #             )
# #         )

# #         # =====================================================
# #         # STEP 6 — PREVIEW GENERATION
# #         # =====================================================

# #         thumbnail_path = None
# #         preview_path = None

# #         if mime_type.startswith("image"):

# #             thumbnail_path = (
# #                 self.thumbnail_service
# #                 .generate_image_thumbnail(
# #                     original_path,
# #                     filename
# #                 )
# #             )

# #         elif mime_type == "application/pdf":

# #             preview_path = (
# #                 self.pdf_preview_service
# #                 .generate_preview(
# #                     original_path,
# #                     filename
# #                 )
# #             )

# #         elif mime_type.startswith("video"):

# #             preview_path = (
# #                 self.video_preview_service
# #                 .generate_preview(
# #                     original_path,
# #                     filename
# #                 )
# #             )

# #         # =====================================================
# #         # STEP 7 — VERSIONING
# #         # =====================================================

# #         version = 1

# #         root_asset_id = None

# #         if parent_id:

# #             old_asset = (
# #                 db.query(Asset)
# #                 .filter(
# #                     Asset.id == parent_id,
# #                     Asset.is_latest == True
# #                 )
# #                 .first()
# #             )

# #             if old_asset:

# #                 old_asset.is_latest = False

# #                 version = old_asset.version + 1

# #                 root_asset_id = (
# #                     old_asset.root_asset_id
# #                     or old_asset.id
# #                 )

# #         # =====================================================
# #         # STEP 8 — INSERT DB RECORD
# #         # =====================================================

# #         asset = Asset(

# #             original_filename=file.filename,

# #             stored_filename=filename,

# #             mime_type=mime_type,

# #             file_size=len(content),

# #             file_hash=file_hash,

# #             storage_path=original_path,

# #             thumbnail_path=thumbnail_path,

# #             preview_path=preview_path,

# #             asset_metadata=metadata,

# #             status=status,

# #             version=version,

# #             parent_id=parent_id,

# #             root_asset_id=root_asset_id,

# #             is_latest=True
# #         )

# #         db.add(asset)

# #         db.flush()

# #         if not asset.root_asset_id:
# #             asset.root_asset_id = asset.id

# #         db.commit()

# #         db.refresh(asset)

# #         # =====================================================
# #         # STEP 9 — FUTURE AI ENRICHMENT
# #         # =====================================================

# #         try:
# #             file_extension = (
# #                 filename.split(".")[-1].lower()
# #             )

# #             # RUN AI PIPELINE
# #             ai_metadata = self.enrichment_pipeline.process_asset(
# #                 asset_type=file_extension,
# #                 file_path=original_path
# #             )

# #             # EXISTING USER METADATA
# #             existing_metadata = dict(asset.asset_metadata or {})

# #             # ENRICH METADATA
# #             existing_metadata["ai_enrichment"] = (ai_metadata)


# #             # UPDATE ASSET METADATA
# #             asset.asset_metadata = existing_metadata

# #             db.commit()
# #             db.refresh(asset)
# #         except Exception as e:
# #             print(f"AI Enrichment failed: {e}")
# #         return asset
# from fastapi import HTTPException

# from sqlalchemy.orm import Session

# from app.models.asset.asset_model import Asset

# from app.services.storage.storage_service import StorageService
# from app.services.storage.thumbnail_service import ThumbnailService
# from app.services.storage.pdf_preview_service import PDFPreviewService
# from app.services.storage.video_preview_service import VideoPreviewService

# from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline
# from app.ai.embeddings.semantic_search_service import SemanticSearchService

# from app.utils.file_utils import (
#     calculate_file_hash,
#     detect_mime_type,
#     validate_mime_type
# )


# class AssetService:

#     def __init__(self):

#         self.storage_service = StorageService()

#         self.thumbnail_service = ThumbnailService()

#         self.pdf_preview_service = PDFPreviewService()

#         self.video_preview_service = VideoPreviewService()

#         self.enrichment_pipeline = EnrichmentPipeline()

#     async def upload_asset(
#         self,
#         file,
#         db: Session,
#         metadata: dict = None,
#         status: str = "draft",
#         parent_id: str = None
#     ):

#         # =====================================================
#         # STEP 1 — SAVE TO TEMP
#         # =====================================================

#         filename, temp_path, content = (
#             await self.storage_service.save_to_temp(file)
#         )

#         # =====================================================
#         # STEP 2 — HASH GENERATION
#         # =====================================================

#         file_hash = calculate_file_hash(content)

#         # =====================================================
#         # STEP 3 — DUPLICATE CHECK
#         # =====================================================

#         existing_asset = (
#             db.query(Asset)
#             .filter(Asset.file_hash == file_hash)
#             .first()
#         )

#         if existing_asset and not parent_id:

#             self.storage_service.delete_temp_file(temp_path)

#             raise HTTPException(
#                 status_code=409,
#                 detail="Duplicate asset already exists"
#             )

#         # =====================================================
#         # STEP 4 — VALIDATION
#         # =====================================================

#         mime_type = detect_mime_type(temp_path)

#         validate_mime_type(mime_type)

#         # =====================================================
#         # STEP 5 — MOVE TO ORIGINALS
#         # =====================================================

#         original_path = (
#             self.storage_service.move_to_original(
#                 temp_path,
#                 filename
#             )
#         )

#         # =====================================================
#         # STEP 6 — PREVIEW GENERATION
#         # =====================================================

#         thumbnail_path = None
#         preview_path = None

#         if mime_type.startswith("image"):

#             thumbnail_path = (
#                 self.thumbnail_service
#                 .generate_image_thumbnail(
#                     original_path,
#                     filename
#                 )
#             )

#         elif mime_type == "application/pdf":

#             preview_path = (
#                 self.pdf_preview_service
#                 .generate_preview(
#                     original_path,
#                     filename
#                 )
#             )

#         elif mime_type.startswith("video"):

#             preview_path = (
#                 self.video_preview_service
#                 .generate_preview(
#                     original_path,
#                     filename
#                 )
#             )

#         # =====================================================
#         # STEP 7 — VERSIONING
#         # =====================================================

#         version = 1

#         root_asset_id = None

#         if parent_id:

#             old_asset = (
#                 db.query(Asset)
#                 .filter(
#                     Asset.id == parent_id,
#                     Asset.is_latest == True
#                 )
#                 .first()
#             )

#             if old_asset:

#                 old_asset.is_latest = False

#                 version = old_asset.version + 1

#                 root_asset_id = (
#                     old_asset.root_asset_id
#                     or old_asset.id
#                 )

#         # =====================================================
#         # STEP 8 — INSERT DB RECORD
#         # =====================================================

#         asset = Asset(

#             original_filename=file.filename,

#             stored_filename=filename,

#             mime_type=mime_type,

#             file_size=len(content),

#             file_hash=file_hash,

#             storage_path=original_path,

#             thumbnail_path=thumbnail_path,

#             preview_path=preview_path,

#             asset_metadata=metadata,

#             status=status,

#             version=version,

#             parent_id=parent_id,

#             root_asset_id=root_asset_id,

#             is_latest=True
#         )

#         db.add(asset)

#         db.flush()

#         if not asset.root_asset_id:
#             asset.root_asset_id = asset.id

#         db.commit()

#         db.refresh(asset)

#         # =====================================================
#         # STEP 9 — AI ENRICHMENT
#         # =====================================================

#         try:
#             file_extension = (
#                 filename.split(".")[-1].lower()
#             )

#             # RUN AI PIPELINE
#             ai_metadata = self.enrichment_pipeline.process_asset(
#                 asset_type=file_extension,
#                 file_path=original_path
#             )

#             # EXISTING USER METADATA
#             existing_metadata = dict(asset.asset_metadata or {})

#             # ENRICH METADATA
#             existing_metadata["ai_enrichment"] = ai_metadata

#             # UPDATE ASSET METADATA
#             asset.asset_metadata = existing_metadata

#             db.commit()
#             db.refresh(asset)

#         except Exception as e:
#             print(f"AI Enrichment failed: {e}")

#         # =====================================================
#         # STEP 10 — SEMANTIC INDEXING
#         # Only index approved assets into the vector store.
#         # Draft assets are indexed when they are approved.
#         # Re-uploads (versioning) reindex using the same asset_id
#         # so the old vector is overwritten automatically.
#         # =====================================================

#         try:
#             if asset.asset_metadata:
#                 SemanticSearchService.index_asset(
#                     asset_id=str(asset.id),
#                     asset=asset.asset_metadata,
#                     status=asset.status,
#                 )

#         except Exception as e:
#             # Non-fatal — asset is saved, search indexing can be
#             # retried manually via the reindex endpoint.
#             print(f"Semantic indexing failed for asset {asset.id}: {e}")

#         return asset

#     async def approve_asset(
#         self,
#         asset_id: str,
#         db: Session,
#     ):
#         """
#         Called by Reviewer/Admin when approving an asset.
#         Updates DB status to approved and reindexes in vector store
#         so the asset becomes searchable (per PDF workflow: Step 3).
#         """

#         asset = (
#             db.query(Asset)
#             .filter(Asset.id == asset_id)
#             .first()
#         )

#         if not asset:
#             raise HTTPException(status_code=404, detail="Asset not found")

#         asset.status = "approved"

#         db.commit()
#         db.refresh(asset)

#         # Reindex so status="approved" is reflected in vector store,
#         # making it visible in semantic search results.
#         try:
#             if asset.asset_metadata:
#                 SemanticSearchService.reindex_asset(
#                     asset_id=str(asset.id),
#                     asset=asset.asset_metadata,
#                     status="approved",
#                 )

#         except Exception as e:
#             print(f"Reindex after approval failed for asset {asset.id}: {e}")

#         return asset

#     async def archive_asset(
#         self,
#         asset_id: str,
#         db: Session,
#     ):
#         """
#         Called by Admin/Super Admin to archive an expired/unused asset.
#         Reindexes with status="archived" so it is excluded from
#         default semantic search (per PDF workflow: Step 6 Archive Flow).
#         """

#         asset = (
#             db.query(Asset)
#             .filter(Asset.id == asset_id)
#             .first()
#         )

#         if not asset:
#             raise HTTPException(status_code=404, detail="Asset not found")

#         asset.status = "archived"
#         asset.is_archived = True

#         db.commit()
#         db.refresh(asset)

#         # Reindex with archived status — search_approved_only() will
#         # exclude this asset from all default searches automatically.
#         try:
#             if asset.asset_metadata:
#                 SemanticSearchService.reindex_asset(
#                     asset_id=str(asset.id),
#                     asset=asset.asset_metadata,
#                     status="archived",
#                 )

#         except Exception as e:
#             print(f"Reindex after archive failed for asset {asset.id}: {e}")

#         return asset
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

from app.services.storage.storage_service import StorageService
from app.services.storage.thumbnail_service import ThumbnailService
from app.services.storage.pdf_preview_service import PDFPreviewService
from app.services.storage.video_preview_service import VideoPreviewService

from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline
from app.ai.embeddings.semantic_search_service import SemanticSearchService

from app.utils.file_utils import (
    calculate_file_hash,
    detect_mime_type,
    validate_mime_type
)


class AssetService:

    def __init__(self):

        self.storage_service = StorageService()

        self.thumbnail_service = ThumbnailService()

        self.pdf_preview_service = PDFPreviewService()

        self.video_preview_service = VideoPreviewService()

        self.enrichment_pipeline = EnrichmentPipeline()

    async def upload_asset(
        self,
        file,
        db: Session,
        metadata: dict = None,
        status: str = "draft",
        parent_id: str = None
    ):

        # =====================================================
        # STEP 1 — SAVE TO TEMP
        # =====================================================

        filename, temp_path, content = (
            await self.storage_service.save_to_temp(file)
        )

        # =====================================================
        # STEP 2 — HASH GENERATION
        # =====================================================

        file_hash = calculate_file_hash(content)

        # =====================================================
        # STEP 3 — DUPLICATE CHECK
        # =====================================================

        existing_asset = (
            db.query(Asset)
            .filter(Asset.file_hash == file_hash)
            .first()
        )

        if existing_asset and not parent_id:

            self.storage_service.delete_temp_file(temp_path)

            raise HTTPException(
                status_code=409,
                detail="Duplicate asset already exists"
            )

        # =====================================================
        # STEP 4 — VALIDATION
        # =====================================================

        mime_type = detect_mime_type(temp_path)

        validate_mime_type(mime_type)

        # =====================================================
        # STEP 5 — MOVE TO ORIGINALS
        # =====================================================

        original_path = (
            self.storage_service.move_to_original(
                temp_path,
                filename
            )
        )

        # =====================================================
        # STEP 6 — PREVIEW GENERATION
        # =====================================================

        thumbnail_path = None
        preview_path = None

        if mime_type.startswith("image"):

            thumbnail_path = (
                self.thumbnail_service
                .generate_image_thumbnail(
                    original_path,
                    filename
                )
            )

        elif mime_type == "application/pdf":

            preview_path = (
                self.pdf_preview_service
                .generate_preview(
                    original_path,
                    filename
                )
            )

        elif mime_type.startswith("video"):

            preview_path = (
                self.video_preview_service
                .generate_preview(
                    original_path,
                    filename
                )
            )

        # =====================================================
        # STEP 7 — VERSIONING
        # =====================================================

        version = 1

        root_asset_id = None

        if parent_id:

            old_asset = (
                db.query(Asset)
                .filter(
                    Asset.id == parent_id,
                    Asset.is_latest == True
                )
                .first()
            )

            if old_asset:

                old_asset.is_latest = False

                version = old_asset.version + 1

                root_asset_id = (
                    old_asset.root_asset_id
                    or old_asset.id
                )

        # =====================================================
        # STEP 8 — INSERT DB RECORD
        # =====================================================

        asset = Asset(

            original_filename=file.filename,

            stored_filename=filename,

            mime_type=mime_type,

            file_size=len(content),

            file_hash=file_hash,

            storage_path=original_path,

            thumbnail_path=thumbnail_path,

            preview_path=preview_path,

            asset_metadata=metadata,

            status=status,

            version=version,

            parent_id=parent_id,

            root_asset_id=root_asset_id,

            is_latest=True
        )

        db.add(asset)

        db.flush()

        if not asset.root_asset_id:
            asset.root_asset_id = asset.id

        db.commit()

        db.refresh(asset)

        # =====================================================
        # STEP 9 — AI ENRICHMENT
        # =====================================================

        try:
            file_extension = (
                filename.split(".")[-1].lower()
            )

            # RUN AI PIPELINE
            ai_metadata = self.enrichment_pipeline.process_asset(
                asset_type=file_extension,
                file_path=original_path
            )

            # EXISTING USER METADATA
            existing_metadata = dict(asset.asset_metadata or {})

            # ENRICH METADATA
            existing_metadata["ai_enrichment"] = ai_metadata

            # UPDATE ASSET METADATA
            asset.asset_metadata = existing_metadata

            db.commit()
            db.refresh(asset)

        except Exception as e:
            print(f"AI Enrichment failed: {e}")

        # =====================================================
        # STEP 10 — SEMANTIC INDEXING
        # Only index approved assets into the vector store.
        # Draft assets are indexed when they are approved.
        # Re-uploads (versioning) reindex using the same asset_id
        # so the old vector is overwritten automatically.
        # =====================================================

        try:
            if asset.asset_metadata:
                SemanticSearchService.index_asset(
                    asset_id=str(asset.id),
                    asset_metadata=asset.asset_metadata,
                    status=asset.status,
                )

        except Exception as e:
            # Non-fatal — asset is saved, search indexing can be
            # retried manually via the reindex endpoint.
            print(f"Semantic indexing failed for asset {asset.id}: {e}")

        return asset

    async def approve_asset(
        self,
        asset_id: str,
        db: Session,
    ):
        """
        Called by Reviewer/Admin when approving an asset.
        Updates DB status to approved and reindexes in vector store
        so the asset becomes searchable (per PDF workflow: Step 3).
        """

        asset = (
            db.query(Asset)
            .filter(Asset.id == asset_id)
            .first()
        )

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset.status = "approved"

        db.commit()
        db.refresh(asset)

        # Reindex so status="approved" is reflected in vector store,
        # making it visible in semantic search results.
        try:
            if asset.asset_metadata:
                SemanticSearchService.reindex_asset(
                    asset_id=str(asset.id),
                    asset_metadata=asset.asset_metadata,
                    status="approved",
                )

        except Exception as e:
            print(f"Reindex after approval failed for asset {asset.id}: {e}")

        return asset

    async def archive_asset(
        self,
        asset_id: str,
        db: Session,
    ):
        """
        Called by Admin/Super Admin to archive an expired/unused asset.
        Reindexes with status="archived" so it is excluded from
        default semantic search (per PDF workflow: Step 6 Archive Flow).
        """

        asset = (
            db.query(Asset)
            .filter(Asset.id == asset_id)
            .first()
        )

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset.status = "archived"
        asset.is_archived = True

        db.commit()
        db.refresh(asset)

        try:
            if asset.asset_metadata:
                SemanticSearchService.reindex_asset(
                    asset_id=str(asset.id),
                    asset_metadata=asset.asset_metadata,
                    status="archived",
                )

        except Exception as e:
            print(f"Reindex after archive failed for asset {asset.id}: {e}")

        return asset