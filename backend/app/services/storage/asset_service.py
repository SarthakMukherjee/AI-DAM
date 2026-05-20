from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

from app.services.storage.storage_service import StorageService
from app.services.storage.thumbnail_service import ThumbnailService
from app.services.storage.pdf_preview_service import PDFPreviewService
from app.services.storage.video_preview_service import VideoPreviewService

from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline

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
        # STEP 9 — FUTURE AI ENRICHMENT
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
            existing_metadata["ai_enrichment"] = (ai_metadata)


            # UPDATE ASSET METADATA
            asset.asset_metadata = existing_metadata

            db.commit()
            db.refresh(asset)
        except Exception as e:
            print(f"AI Enrichment failed: {e}")
        return asset