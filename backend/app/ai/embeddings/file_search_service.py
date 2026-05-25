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