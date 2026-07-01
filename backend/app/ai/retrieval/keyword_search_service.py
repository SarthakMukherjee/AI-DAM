from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String

from app.models.asset.asset_model import Asset


STOPWORDS = {
    "for",
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "with",
    "suitable",
}


def _ilike(field, term: str):
    return field.ilike(f"%{term}%")


def _jsonb_ilike(column, *keys, term: str):
    field = column

    for key in keys:
        field = field[key]

    return cast(field, String).ilike(f"%{term}%")


def _apply_facet_filters(base_query, filters: dict):
    """
    Apply faceted filters to a SQLAlchemy query on the Asset model.

    Supported filter keys:
        domain      → asset_metadata.business.domain
        status      → Asset.status
        asset_type  → asset_metadata.mandatory.asset_type
        geography   → asset_metadata.business.geography
        campaign    → asset_metadata.business.campaign
        language    → asset_metadata.business.language
    """
    if not filters:
        return base_query

    m = Asset.asset_metadata

    if filters.get("status"):
        base_query = base_query.filter(
            Asset.status == filters["status"]
        )

    if filters.get("asset_type"):
        base_query = base_query.filter(
            cast(m["mandatory"]["asset_type"], String).ilike(
                f'%{filters["asset_type"]}%'
            )
        )

    if filters.get("domain"):
        base_query = base_query.filter(
            cast(m["business"]["domain"], String).ilike(
                f'%{filters["domain"]}%'
            )
        )

    if filters.get("geography"):
        base_query = base_query.filter(
            cast(m["business"]["geography"], String).ilike(
                f'%{filters["geography"]}%'
            )
        )

    if filters.get("campaign"):
        base_query = base_query.filter(
            cast(m["business"]["campaign"], String).ilike(
                f'%{filters["campaign"]}%'
            )
        )

    if filters.get("language"):
        base_query = base_query.filter(
            cast(m["business"]["language"], String).ilike(
                f'%{filters["language"]}%'
            )
        )

    return base_query


def _build_field_scoped_filter(m, term: str, search_field: str | None):
    """
    If search_field is given, return an ilike filter scoped to that field only.
    Falls back to None (caller should use full-field set) if field is unknown.
    """
    field_map = {
        "asset_name":       lambda: _jsonb_ilike(m, "mandatory", "asset_name",    term=term),
        "description":      lambda: _jsonb_ilike(m, "mandatory", "description",   term=term),
        "campaign":         lambda: _jsonb_ilike(m, "business",  "campaign",       term=term),
        "ai_tags":          lambda: _jsonb_ilike(m, "ai_enrichment", "ai_tags",   term=term),
        "extracted_text":   lambda: _jsonb_ilike(m, "ai_enrichment", "extracted_text", term=term),
        "image_caption":    lambda: _jsonb_ilike(m, "ai_enrichment", "image_caption",  term=term),
        "keywords":         lambda: _jsonb_ilike(m, "content", "keywords",         term=term),
    }
    if search_field and search_field in field_map:
        return field_map[search_field]()
    return None


class KeywordSearchService:

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 20,
        approved_only: bool = True,
        filters: dict | None = None,
        search_field: str | None = None,
    ) -> list[dict]:

        terms = [
            t.strip()
            for t in query.split()
            if t.strip()
            and t.lower() not in STOPWORDS
        ]

        if not terms:
            return []

        base_query = (
            db.query(Asset)
            .filter(Asset.is_latest == True)
        )

        if approved_only:
            base_query = (
                base_query.filter(
                    Asset.status == "approved"
                )
            )

        # Apply faceted filters (post approved_only, pre text search)
        base_query = _apply_facet_filters(base_query, filters or {})

        for term in terms:

            m = Asset.asset_metadata

            # If a specific field is requested, scope search to it only
            scoped = _build_field_scoped_filter(m, term, search_field)

            if scoped is not None:
                base_query = base_query.filter(scoped)
            else:
                # Default: search across all relevant fields
                base_query = base_query.filter(or_(

                    _ilike(Asset.id, term),

                    _ilike(
                        Asset.original_filename,
                        term
                    ),

                    _ilike(
                        Asset.mime_type,
                        term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "asset_name",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "description",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "asset_type",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "owner",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "created_by",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "mandatory",
                        "usage_rights",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "domain",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "use_case",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "audience",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "funnel_stage",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "campaign",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "geography",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "business",
                        "language",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "content",
                        "tone",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "content",
                        "keywords",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "content",
                        "visual_elements",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "ai_enrichment",
                        "ai_tags",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "ai_enrichment",
                        "searchable_tags",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "ai_enrichment",
                        "extracted_text",
                        term=term
                    ),

                    _jsonb_ilike(
                        m,
                        "ai_enrichment",
                        "image_caption",
                        term=term
                    ),
                ))

        assets = base_query.limit(limit).all()

        return [
            _format_asset(asset, query)
            for asset in assets
        ]


def _keyword_score(
    asset: Asset,
    query: str
) -> float:

    m = asset.asset_metadata or {}

    ai = m.get("ai_enrichment") or {}

    man = m.get("mandatory") or {}

    con = m.get("content") or {}

    searchable = " ".join([

        man.get("asset_name", ""),

        man.get("description", ""),

        str(ai.get("ai_tags", "")),

        str(ai.get("searchable_tags", "")),

        str(con.get("keywords", "")),

        asset.original_filename or "",

    ]).lower()

    terms = [

        t.lower()

        for t in query.split()

        if t.strip()
        and t.lower() not in STOPWORDS
    ]

    matched = sum(
        1
        for t in terms
        if t in searchable
    )

    return round(
        matched / max(len(terms), 1),
        4
    )


def _format_asset(
    asset: Asset,
    query: str
) -> dict:

    return {

        "asset_id":
            str(asset.id),

        "keyword_score":
            _keyword_score(asset, query),

        "original_filename":
            asset.original_filename or "",

        "storage_path":
            asset.storage_path or "",

        "thumbnail_path":
            asset.thumbnail_path,

        "preview_path":
            asset.preview_path,

        "mime_type":
            asset.mime_type or "",

        "status":
            asset.status,

        "asset_metadata":
            asset.asset_metadata or {},

        "completeness_score":
            asset.completeness_score or 0,

        "ai_summary":
            asset.ai_summary,

        "perceptual_hash":
            asset.perceptual_hash,
    }