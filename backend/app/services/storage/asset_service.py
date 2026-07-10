import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

from app.services.storage.storage_service import StorageService
from app.services.storage.thumbnail_service import ThumbnailService
from app.services.storage.pdf_preview_service import PDFPreviewService
from app.services.storage.video_preview_service import VideoPreviewService
from app.services.storage.cloud_service import CloudService
from app.ai.retrieval.semantic_search_service import SemanticSearchService
from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline

from app.utils.file_utils import (
    calculate_file_hash,
    detect_mime_type,
    validate_mime_type
)
from app.utils.image_hash import compute_dhash
from app.utils.completeness import calculate_completeness


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
        parent_id: str = None,
        changelog: str = None,
        uploaded_by: str = None,
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
        # STEP 3 — DUPLICATE CHECK (exact hash)
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
        # STEP 5 — PERCEPTUAL HASH (images only, before move)
        # =====================================================

        perceptual_hash = None
        if mime_type.startswith("image/"):
            perceptual_hash = compute_dhash(temp_path)
            if perceptual_hash:
                print(f"[PERCEPTUAL HASH] {perceptual_hash} for {filename}")

        # =====================================================
        # STEP 6 — MOVE TO LOCAL ORIGINALS
        # =====================================================

        original_path = self.storage_service.move_to_original(
            temp_path,
            filename
        )

        # =====================================================
        # STEP 7 — CONFIGURATION & RESOURCE MAPPING
        # =====================================================

        asset_id_temp = filename.split(".")[0]

        if mime_type == "application/pdf":
            resource_type = "image"
        elif mime_type.startswith("image/"):
            resource_type = "image"
        elif mime_type.startswith("video/"):
            resource_type = "video"
        else:
            resource_type = "raw"

        # =====================================================
        # STEP 8 — PREVIEW GENERATION (before cloud upload)
        # local file still exists here
        # =====================================================

        thumbnail_path = None
        preview_path = None

        if mime_type.startswith("image"):
            local_thumb = self.thumbnail_service.generate_image_thumbnail(
                original_path, filename
            )
            if local_thumb:
                cloud_thumb = CloudService.upload(
                    file_path=local_thumb,
                    public_id=f"thumbnails/{asset_id_temp}",
                    resource_type="image",
                    folder="ai-dam"
                )
                thumbnail_path = cloud_thumb
                self.storage_service.delete_local_file(local_thumb)

        elif mime_type == "application/pdf":
            local_preview = self.pdf_preview_service.generate_preview(
                original_path, filename
            )
            if local_preview:
                cloud_preview = CloudService.upload(
                    file_path=local_preview,
                    public_id=f"previews/{asset_id_temp}_page1",
                    resource_type="image",
                    folder="ai-dam"
                )
                preview_path = cloud_preview
                self.storage_service.delete_local_file(local_preview)

        elif mime_type.startswith("video"):
            local_preview = self.video_preview_service.generate_preview(
                original_path, filename
            )
            if local_preview:
                cloud_preview = CloudService.upload(
                    file_path=local_preview,
                    public_id=f"previews/{asset_id_temp}_thumb",
                    resource_type="image",
                    folder="ai-dam"
                )
                preview_path = cloud_preview
                self.storage_service.delete_local_file(local_preview)

        # =====================================================
        # =====================================================
        # STEP 9 — UPLOAD ORIGINAL TO STORAGE BACKEND
        # =====================================================
        print(f"[UPLOAD] Persisting to storage backend: {original_path}")

        cloud_url = CloudService.upload(
            file_path=original_path,
            public_id=f"originals/{asset_id_temp}",
            resource_type=resource_type,
            folder="ai-dam"
        )

        print(f"[UPLOAD] Storage result: {cloud_url}")

        if not cloud_url:
            self.storage_service.delete_local_file(original_path)
            raise HTTPException(
                status_code=500,
                detail="File upload to cloud storage failed. Please try again."
            )

        storage_path = cloud_url

        # NOW safe to delete local original
        self.storage_service.delete_local_file(original_path)

        # =====================================================
        # STEP 10 — VERSIONING
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
                root_asset_id = old_asset.root_asset_id or old_asset.id

        # =====================================================
        # STEP 11 — METADATA COMPLETENESS SCORE
        # =====================================================

        completeness_score = calculate_completeness(metadata or {})

        # =====================================================
        # STEP 12 — INSERT DB RECORD
        # =====================================================

        asset = Asset(
            original_filename=file.filename,
            stored_filename=filename,
            mime_type=mime_type,
            file_size=len(content),
            file_hash=file_hash,
            storage_path=storage_path,
            thumbnail_path=thumbnail_path,
            preview_path=preview_path,
            asset_metadata=metadata,
            status=status,
            version=version,
            parent_id=parent_id,
            root_asset_id=root_asset_id,
            is_latest=True,
            perceptual_hash=perceptual_hash,
            completeness_score=completeness_score,
            changelog=changelog,
            updated_by=uploaded_by,
        )

        db.add(asset)
        db.flush()

        if not asset.root_asset_id:
            asset.root_asset_id = asset.id

        db.commit()
        db.refresh(asset)

        # =====================================================
        # STEP 13 — AI ENRICHMENT
        # =====================================================

        try:
            file_extension = filename.split(".")[-1].lower()

            ai_metadata = self.enrichment_pipeline.process_asset(
                asset_type=file_extension,
                file_path=storage_path  # use cloud URL not local path
            )

            existing_metadata = dict(asset.asset_metadata or {})
            existing_metadata["ai_enrichment"] = ai_metadata
            
            # Map ai_summary to mandatory description if default from batch upload
            desc = existing_metadata.get("mandatory", {}).get("description", "")
            if not desc or desc.startswith("Batch uploaded:") or desc == "Wait for AI":
                if ai_metadata.get("ai_summary"):
                    if "mandatory" not in existing_metadata:
                        existing_metadata["mandatory"] = {}
                    existing_metadata["mandatory"]["description"] = ai_metadata.get("ai_summary")
            
            asset.asset_metadata = existing_metadata

            # ─────────────────────────────────────────────
            # Populate queryable AI columns from enrichment
            # ─────────────────────────────────────────────
            asset.ai_tags          = ai_metadata.get("ai_tags") or []
            asset.detected_objects = ai_metadata.get("detected_objects") or []
            asset.extracted_text   = ai_metadata.get("extracted_text") or None
            asset.image_caption    = ai_metadata.get("image_caption") or None
            asset.ai_summary       = ai_metadata.get("ai_summary") or None

            db.commit()
            db.refresh(asset)

        except Exception as e:
            print(f"[AI ENRICHMENT] Failed: {e}")

        # =====================================================
        # STEP 14 — SEMANTIC INDEXING
        # =====================================================

        try:
            SemanticSearchService.index_asset(
                asset_id=str(asset.id),
                asset_metadata=asset.asset_metadata or {},
                status=asset.status
            )
            print(f"[SEMANTIC INDEXED] Asset ID: {asset.id}")

        except Exception as e:
            print(f"[SEMANTIC INDEX FAILED] Asset ID: {asset.id} | Error: {e}")

        # =====================================================
        # STEP 15 — RETURN ASSET
        # =====================================================

        return asset