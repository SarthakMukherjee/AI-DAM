from sqlalchemy.orm import Session

from app.ai.embeddings.embedding_utils import embed_asset, generate_embedding
from app.ai.vectorstore.vector_upsert_service import VectorUpsertService
from app.ai.vectorstore.vector_query_service import VectorQueryService
from app.models.asset.asset_model import Asset


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, 1.0 - (distance / 2.0)), 4)


def _fetch_assets_by_ids(
    asset_ids: list[str],
    db: Session
) -> dict[str, Asset]:
    """Fetch full asset records from PostgreSQL by ID list."""
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    return {str(a.id): a for a in assets}


def _format_results(raw: dict, db: Session) -> list[dict]:
    """
    Merges ChromaDB scores with full PostgreSQL asset data.
    Assets deleted from PostgreSQL but still in ChromaDB are skipped.
    """
    ids       = raw.get("ids", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    # Fetch full data from PostgreSQL
    asset_map = _fetch_assets_by_ids(ids, db)

    results = []
    for asset_id, distance in zip(ids, distances):
        asset = asset_map.get(asset_id)
        if not asset:
            continue  # stale vector — asset deleted from DB

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


class SemanticSearchService:

    # -----------------------------------------------------------------------
    # INDEXING
    # -----------------------------------------------------------------------

    @staticmethod
    def index_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved",
    ) -> bool:
        document, embedding = embed_asset(asset_metadata)

        VectorUpsertService.upsert_embedding(
            asset_id=asset_id,
            embedding=embedding,
            document=document,
            asset=asset_metadata,
            status=status,
        )
        return True

    @staticmethod
    def reindex_asset(
        asset_id: str,
        asset_metadata: dict,
        status: str = "approved",
    ) -> bool:
        return SemanticSearchService.index_asset(asset_id, asset_metadata, status)

    # -----------------------------------------------------------------------
    # SEARCHING
    # -----------------------------------------------------------------------

    @staticmethod
    def search(
        query: str,
        db: Session,
        limit: int = 10,
        approved_only: bool = True,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Semantic search: embed query → ChromaDB → fetch full data from PostgreSQL.

        Args:
            query:         Natural language query
            db:            SQLAlchemy session (to fetch full asset data)
            limit:         Max results
            approved_only: Only return approved assets
            filters:       Optional ChromaDB metadata filters
        """
        query_embedding = generate_embedding(query)

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

        return _format_results(raw, db)