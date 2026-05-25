# # # file_search_service.py
# # # Semantic search by file upload.
# # #
# # # Flow:
# # #   1. Save uploaded file to temp
# # #   2. Run through EnrichmentPipeline (same as upload)
# # #      → extracts tags, caption, objects, text
# # #   3. Build semantic document from extracted data
# # #   4. Embed the document
# # #   5. Query ChromaDB for similar assets
# # #   6. Return ranked results

# # import os
# # import uuid
# # import shutil

# # from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline
# # from app.ai.embeddings.embedding_utils import (
# #     build_semantic_document,
# #     generate_embedding,
# # )
# # from app.ai.vectorstore.vector_query_service import VectorQueryService


# # # Temp dir for search uploads — separate from asset storage
# # SEARCH_TEMP_DIR = "storage/search_temp"


# # def _get_file_extension(filename: str) -> str:
# #     """Extract lowercase extension from filename."""
# #     return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


# # def _save_temp(file_bytes: bytes, filename: str) -> str:
# #     """
# #     Save uploaded file bytes to a temp path for processing.
# #     Returns the temp file path.
# #     """
# #     os.makedirs(SEARCH_TEMP_DIR, exist_ok=True)
# #     temp_name = f"{uuid.uuid4()}_{filename}"
# #     temp_path = os.path.join(SEARCH_TEMP_DIR, temp_name)
# #     with open(temp_path, "wb") as f:
# #         f.write(file_bytes)
# #     return temp_path


# # def _cleanup_temp(temp_path: str):
# #     """Delete temp file after processing."""
# #     try:
# #         if os.path.exists(temp_path):
# #             os.remove(temp_path)
# #     except Exception as e:
# #         print(f"Temp cleanup failed: {e}")


# # def _build_query_asset(ai_enrichment: dict) -> dict:
# #     """
# #     Wraps AI enrichment output into the asset dict shape
# #     that build_semantic_document() expects.

# #     Since this is a search query (not a stored asset),
# #     mandatory/business/content fields are empty —
# #     the semantic signal comes entirely from the AI-extracted tags.
# #     """
# #     return {
# #         "mandatory": {
# #             "asset_name": "",
# #             "asset_type": "",
# #             "description": "",
# #             "created_by": "",
# #             "usage_rights": "",
# #             "owner": "",
# #         },
# #         "business": {
# #             "domain": "",
# #             "use_case": "",
# #             "audience": "",
# #             "funnel_stage": "",
# #         },
# #         "content": {
# #             "keywords": [],
# #             "visual_elements": [],
# #             "tone": "",
# #         },
# #         "ai_enrichment": ai_enrichment,
# #     }


# # class FileSearchService:

# #     def __init__(self):
# #         self.enrichment_pipeline = EnrichmentPipeline()

# #     def search_by_file(
# #         self,
# #         file_bytes: bytes,
# #         filename: str,
# #         limit: int = 10,
# #         approved_only: bool = True,
# #         filters: dict | None = None,
# #     ) -> dict:
# #         """
# #         Main entry point: takes an uploaded file, extracts semantic
# #         signals via AI pipeline, and returns similar assets from ChromaDB.

# #         Args:
# #             file_bytes:    Raw bytes of the uploaded file
# #             filename:      Original filename (used to detect type)
# #             limit:         Max results to return
# #             approved_only: Only return approved assets
# #             filters:       Optional metadata filters
# #                            e.g. {"asset_type": "banner", "domain": "ai_services"}

# #         Returns:
# #             {
# #                 "filename":        str,
# #                 "enrichment":      dict,   # what the AI extracted
# #                 "total":           int,
# #                 "results":         list[dict],
# #             }
# #         """

# #         temp_path = None

# #         try:

# #             # ================================================
# #             # STEP 1 — SAVE TO TEMP
# #             # ================================================

# #             temp_path = _save_temp(file_bytes, filename)

# #             extension = _get_file_extension(filename)

# #             # ================================================
# #             # STEP 2 — RUN AI ENRICHMENT PIPELINE
# #             # Same pipeline as upload — extract tags, caption,
# #             # objects, text from the query file
# #             # ================================================

# #             ai_enrichment = self.enrichment_pipeline.process_asset(
# #                 asset_type=extension,
# #                 file_path=temp_path,
# #             )

# #             if ai_enrichment.get("enrichment_status") == "unsupported_type":
# #                 return {
# #                     "filename": filename,
# #                     "enrichment": ai_enrichment,
# #                     "total": 0,
# #                     "results": [],
# #                     "error": f"Unsupported file type: .{extension}",
# #                 }

# #             # ================================================
# #             # STEP 3 — BUILD SEMANTIC DOCUMENT
# #             # Wrap enrichment in asset shape, build text doc
# #             # ================================================

# #             query_asset = _build_query_asset(ai_enrichment)
# #             semantic_document = build_semantic_document(query_asset)

# #             # ================================================
# #             # STEP 4 — EMBED
# #             # ================================================

# #             query_embedding = generate_embedding(semantic_document)

# #             # ================================================
# #             # STEP 5 — QUERY CHROMADB
# #             # ================================================

# #             if approved_only:
# #                 raw = VectorQueryService.search_approved_only(
# #                     query_embedding=query_embedding,
# #                     limit=limit,
# #                     extra_filters=filters,
# #                 )
# #             else:
# #                 where = None
# #                 if filters:
# #                     if len(filters) == 1:
# #                         where = filters
# #                     else:
# #                         where = {"$and": [{k: v} for k, v in filters.items()]}

# #                 raw = VectorQueryService.semantic_search(
# #                     query_embedding=query_embedding,
# #                     limit=limit,
# #                     where=where,
# #                 )

# #             # ================================================
# #             # STEP 6 — FORMAT RESULTS
# #             # ================================================

# #             results = _format_results(raw)

# #             return {
# #                 "filename": filename,
# #                 "enrichment": ai_enrichment,
# #                 "total": len(results),
# #                 "results": results,
# #             }

# #         finally:
# #             # Always clean up temp file
# #             if temp_path:
# #                 _cleanup_temp(temp_path)


# # # ---------------------------------------------------------------------------
# # # Result formatter (mirrors semantic_search_service._format_results)
# # # ---------------------------------------------------------------------------

# # def _distance_to_score(distance: float) -> float:
# #     score = max(0.0, 1.0 - (distance / 2.0))
# #     return round(score, 4)


# # def _format_results(raw: dict) -> list[dict]:
# #     ids       = raw.get("ids", [[]])[0]
# #     distances = raw.get("distances", [[]])[0]
# #     metadatas = raw.get("metadatas", [[]])[0]
# #     documents = raw.get("documents", [[]])[0]

# #     results = []
# #     for asset_id, distance, meta, doc in zip(ids, distances, metadatas, documents):
# #         results.append({
# #             "asset_id":      asset_id,
# #             "score":         _distance_to_score(distance),
# #             "asset_name":    meta.get("asset_name", ""),
# #             "asset_type":    meta.get("asset_type", ""),
# #             "domain":        meta.get("domain", ""),
# #             "use_case":      meta.get("use_case", ""),
# #             "audience":      meta.get("audience", ""),
# #             "funnel_stage":  meta.get("funnel_stage", ""),
# #             "tone":          meta.get("tone", ""),
# #             "owner":         meta.get("owner", ""),
# #             "status":        meta.get("status", ""),
# #             "ai_tags":       [t.strip() for t in meta.get("ai_tags", "").split(",") if t.strip()],
# #             "image_caption": meta.get("image_caption", ""),
# #         })

# #     return results
# # file_search_service.py
# # Semantic search by file upload.
# #
# # Flow:
# #   1. Save uploaded file to temp
# #   2. Run EnrichmentPipeline (same as upload) → extract tags
# #   3. Build semantic document from extracted ai_enrichment
# #   4. Embed the document
# #   5. Query ChromaDB for similar assets
# #   6. Return ranked results

# import os
# import uuid

# from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline
# from app.ai.embeddings.embedding_utils import (
#     build_semantic_document,
#     generate_embedding,
# )
# from app.ai.vectorstore.vector_query_service import VectorQueryService

# SEARCH_TEMP_DIR = "storage/search_temp"


# def _get_file_extension(filename: str) -> str:
#     return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


# def _save_temp(file_bytes: bytes, filename: str) -> str:
#     os.makedirs(SEARCH_TEMP_DIR, exist_ok=True)
#     temp_name = f"{uuid.uuid4()}_{filename}"
#     temp_path = os.path.join(SEARCH_TEMP_DIR, temp_name)
#     with open(temp_path, "wb") as f:
#         f.write(file_bytes)
#     return temp_path


# def _cleanup_temp(temp_path: str):
#     try:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#     except Exception as e:
#         print(f"Temp cleanup failed: {e}")


# def _distance_to_score(distance: float) -> float:
#     return round(max(0.0, 1.0 - (distance / 2.0)), 4)


# def _format_results(raw: dict) -> list[dict]:
#     ids       = raw.get("ids", [[]])[0]
#     distances = raw.get("distances", [[]])[0]
#     metadatas = raw.get("metadatas", [[]])[0]
#     documents = raw.get("documents", [[]])[0]

#     results = []
#     for asset_id, distance, meta, doc in zip(ids, distances, metadatas, documents):
#         results.append({
#             "asset_id":      asset_id,
#             "score":         _distance_to_score(distance),
#             "asset_name":    meta.get("asset_name", ""),
#             "asset_type":    meta.get("asset_type", ""),
#             "domain":        meta.get("domain", ""),
#             "use_case":      meta.get("use_case", ""),
#             "audience":      meta.get("audience", ""),
#             "funnel_stage":  meta.get("funnel_stage", ""),
#             "tone":          meta.get("tone", ""),
#             "owner":         meta.get("owner", ""),
#             "status":        meta.get("status", ""),
#             "ai_tags":       [t.strip() for t in meta.get("ai_tags", "").split(",") if t.strip()],
#             "image_caption": meta.get("image_caption", ""),
#         })

#     return results


# class FileSearchService:

#     def __init__(self):
#         self.enrichment_pipeline = EnrichmentPipeline()

#     def search_by_file(
#         self,
#         file_bytes: bytes,
#         filename: str,
#         limit: int = 10,
#         approved_only: bool = True,
#         filters: dict | None = None,
#     ) -> dict:
#         """
#         Takes an uploaded file, extracts semantic signals via AI pipeline,
#         and returns similar assets from ChromaDB.
#         """
#         temp_path = None

#         try:
#             # STEP 1 — save to temp
#             temp_path = _save_temp(file_bytes, filename)
#             extension = _get_file_extension(filename)

#             # STEP 2 — run AI enrichment (same pipeline as upload)
#             ai_enrichment = self.enrichment_pipeline.process_asset(
#                 asset_type=extension,
#                 file_path=temp_path,
#             )

#             if ai_enrichment.get("enrichment_status") == "unsupported_type":
#                 return {
#                     "filename": filename,
#                     "enrichment": ai_enrichment,
#                     "total": 0,
#                     "results": [],
#                     "error": f"Unsupported file type: .{extension}",
#                 }

#             # STEP 3 — build asset_metadata shaped dict for build_semantic_document
#             # Only ai_enrichment has real data — mandatory/business/content are empty
#             # since this is a search query, not a stored asset
#             query_asset_metadata = {
#                 "mandatory":  {
#                     "asset_name": "", "asset_type": "", "description": "",
#                     "created_by": "", "usage_rights": "", "owner": "",
#                 },
#                 "business":   {
#                     "domain": "", "use_case": "", "audience": "", "funnel_stage": "",
#                 },
#                 "content":    {"keywords": [], "visual_elements": [], "tone": ""},
#                 "ai_enrichment": ai_enrichment,
#             }

#             # STEP 4 — build semantic document + embed
#             semantic_document = build_semantic_document(query_asset_metadata)
#             query_embedding   = generate_embedding(semantic_document)

#             # STEP 5 — query ChromaDB
#             if approved_only:
#                 raw = VectorQueryService.search_approved_only(
#                     query_embedding=query_embedding,
#                     limit=limit,
#                     extra_filters=filters,
#                 )
#             else:
#                 where = None
#                 if filters:
#                     where = filters if len(filters) == 1 else {
#                         "$and": [{k: v} for k, v in filters.items()]
#                     }
#                 raw = VectorQueryService.semantic_search(
#                     query_embedding=query_embedding,
#                     limit=limit,
#                     where=where,
#                 )

#             # STEP 6 — format and return
#             results = _format_results(raw)

#             return {
#                 "filename":   filename,
#                 "enrichment": ai_enrichment,
#                 "total":      len(results),
#                 "results":    results,
#             }

#         finally:
#             if temp_path:
#                 _cleanup_temp(temp_path)

# file_search_service.py
# Semantic search by file upload.
# File runs through AI enrichment pipeline, then matches against ChromaDB vectors.
# Full asset data fetched from PostgreSQL after vector retrieval.

import os
import uuid

from sqlalchemy.orm import Session

from app.ai.pipelines.enrichment_pipeline import EnrichmentPipeline
from app.ai.embeddings.embedding_utils import build_semantic_document, generate_embedding
from app.ai.vectorstore.vector_query_service import VectorQueryService
from app.models.asset.asset_model import Asset

SEARCH_TEMP_DIR = "storage/search_temp"


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _save_temp(file_bytes: bytes, filename: str) -> str:
    os.makedirs(SEARCH_TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(SEARCH_TEMP_DIR, f"{uuid.uuid4()}_{filename}")
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
    return temp_path


def _cleanup(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Temp cleanup failed: {e}")


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, 1.0 - (distance / 2.0)), 4)


def _fetch_assets(asset_ids: list[str], db: Session) -> dict[str, Asset]:
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    return {str(a.id): a for a in assets}


def _format_results(raw: dict, db: Session) -> list[dict]:
    ids       = raw.get("ids", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    asset_map = _fetch_assets(ids, db)

    results = []
    for asset_id, distance in zip(ids, distances):
        asset = asset_map.get(asset_id)
        if not asset:
            continue
        results.append({
            "asset_id":          asset_id,
            "score":             _distance_to_score(distance),
            "original_filename": asset.original_filename,
            "storage_path":      asset.storage_path or "",
            "thumbnail_path":    asset.thumbnail_path,
            "preview_path":      asset.preview_path,
            "mime_type":         asset.mime_type or "",
            "status":            asset.status,
            "asset_metadata":    asset.asset_metadata or {},
        })
    return results


class FileSearchService:

    def __init__(self):
        self.enrichment_pipeline = EnrichmentPipeline()

    def search_by_file(
        self,
        file_bytes: bytes,
        filename: str,
        db: Session,
        limit: int = 10,
        approved_only: bool = True,
        filters: dict | None = None,
    ) -> dict:

        temp_path = None
        try:
            # STEP 1 — save to temp
            temp_path = _save_temp(file_bytes, filename)
            extension = _get_extension(filename)

            # STEP 2 — AI enrichment (same pipeline as upload)
            ai_enrichment = self.enrichment_pipeline.process_asset(
                asset_type=extension,
                file_path=temp_path,
            )

            if ai_enrichment.get("enrichment_status") == "unsupported_type":
                return {
                    "filename": filename, "enrichment": ai_enrichment,
                    "total": 0, "results": [],
                    "error": f"Unsupported file type: .{extension}",
                }

            # STEP 3 — build semantic document from ai_enrichment only
            query_asset_metadata = {
                "mandatory":     {"asset_name": "", "asset_type": "", "description": "",
                                  "created_by": "", "usage_rights": "", "owner": ""},
                "business":      {"domain": "", "use_case": "", "audience": "", "funnel_stage": ""},
                "content":       {"keywords": [], "visual_elements": [], "tone": ""},
                "ai_enrichment": ai_enrichment,
            }

            # STEP 4 — embed
            semantic_document = build_semantic_document(query_asset_metadata)
            query_embedding   = generate_embedding(semantic_document)

            # STEP 5 — query ChromaDB
            if approved_only:
                raw = VectorQueryService.search_approved_only(
                    query_embedding=query_embedding,
                    limit=limit,
                    extra_filters=filters,
                )
            else:
                where = None
                if filters:
                    where = filters if len(filters) == 1 else {
                        "$and": [{k: v} for k, v in filters.items()]
                    }
                raw = VectorQueryService.semantic_search(
                    query_embedding=query_embedding,
                    limit=limit,
                    where=where,
                )

            # STEP 6 — fetch full data from PostgreSQL
            results = _format_results(raw, db)

            return {
                "filename":   filename,
                "enrichment": ai_enrichment,
                "total":      len(results),
                "results":    results,
            }

        finally:
            if temp_path:
                _cleanup(temp_path)