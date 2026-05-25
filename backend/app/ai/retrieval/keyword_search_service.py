# # # keyword_search_service.py
# # # Keyword search against PostgreSQL JSONB asset_metadata.
# # #
# # # Searches across:
# # #   - original_filename, stored_filename, mime_type (top-level columns)
# # #   - asset_metadata.mandatory: asset_name, description, asset_type, owner
# # #   - asset_metadata.business:  domain, use_case, audience, funnel_stage
# # #   - asset_metadata.content:   tone, keywords[], visual_elements[]
# # #   - asset_metadata.ai_enrichment: ai_tags[], searchable_tags[], extracted_text, image_caption
# # #   - asset id (exact match)

# # from sqlalchemy.orm import Session
# # from sqlalchemy import or_, cast, String
# # from sqlalchemy.dialects.postgresql import JSONB

# # from app.models.asset.asset_model import Asset


# # def _ilike(field, term: str):
# #     """Case-insensitive partial match on a column."""
# #     return field.ilike(f"%{term}%")


# # def _jsonb_ilike(column, *keys, term: str):
# #     """
# #     Case-insensitive partial match on a JSONB nested field.
# #     e.g. asset_metadata -> 'mandatory' -> 'asset_name'
# #     """
# #     field = column
# #     for key in keys:
# #         field = field[key]
# #     return cast(field, String).ilike(f"%{term}%")


# # def _jsonb_array_ilike(column, *keys, term: str):
# #     """
# #     Checks if a JSONB array field contains a string matching the term.
# #     Uses PostgreSQL array_to_string to search inside arrays.
# #     e.g. asset_metadata -> 'content' -> 'keywords' array
# #     """
# #     from sqlalchemy import func
# #     field = column
# #     for key in keys:
# #         field = field[key]
# #     # Cast array to text and search within it
# #     return cast(field, String).ilike(f"%{term}%")


# # class KeywordSearchService:

# #     @staticmethod
# #     def search(
# #         query: str,
# #         db: Session,
# #         limit: int = 20,
# #         approved_only: bool = True,
# #     ) -> list[dict]:
# #         """
# #         Searches all metadata fields in PostgreSQL for the given query.

# #         Splits query into individual terms and matches each term
# #         across all searchable fields using OR logic.
# #         All terms must match at least one field (AND between terms).

# #         Args:
# #             query:         User's search string e.g. "enterprise AI banner"
# #             db:            SQLAlchemy session
# #             limit:         Max results
# #             approved_only: Only return approved assets

# #         Returns:
# #             List of result dicts with keyword_score included.
# #         """

# #         terms = [t.strip() for t in query.split() if t.strip()]

# #         if not terms:
# #             return []

# #         base_query = db.query(Asset).filter(Asset.is_latest == True)

# #         if approved_only:
# #             base_query = base_query.filter(Asset.status == "approved")

# #         # Build filter: each term must match at least one field
# #         for term in terms:
# #             m = Asset.asset_metadata

# #             term_filter = or_(
# #                 # --- top-level columns ---
# #                 _ilike(Asset.id, term),
# #                 _ilike(Asset.original_filename, term),
# #                 _ilike(Asset.mime_type, term),

# #                 # --- mandatory metadata ---
# #                 _jsonb_ilike(m, "mandatory", "asset_name",   term=term),
# #                 _jsonb_ilike(m, "mandatory", "description",  term=term),
# #                 _jsonb_ilike(m, "mandatory", "asset_type",   term=term),
# #                 _jsonb_ilike(m, "mandatory", "owner",        term=term),
# #                 _jsonb_ilike(m, "mandatory", "created_by",   term=term),
# #                 _jsonb_ilike(m, "mandatory", "usage_rights", term=term),

# #                 # --- business metadata ---
# #                 _jsonb_ilike(m, "business", "domain",       term=term),
# #                 _jsonb_ilike(m, "business", "use_case",     term=term),
# #                 _jsonb_ilike(m, "business", "audience",     term=term),
# #                 _jsonb_ilike(m, "business", "funnel_stage", term=term),

# #                 # --- content metadata ---
# #                 _jsonb_ilike(m, "content", "tone",             term=term),
# #                 _jsonb_array_ilike(m, "content", "keywords",        term=term),
# #                 _jsonb_array_ilike(m, "content", "visual_elements", term=term),

# #                 # --- ai enrichment ---
# #                 _jsonb_array_ilike(m, "ai_enrichment", "ai_tags",        term=term),
# #                 _jsonb_array_ilike(m, "ai_enrichment", "searchable_tags", term=term),
# #                 _jsonb_ilike(m, "ai_enrichment", "extracted_text",  term=term),
# #                 _jsonb_ilike(m, "ai_enrichment", "image_caption",   term=term),
# #             )

# #             base_query = base_query.filter(term_filter)

# #         assets = base_query.limit(limit).all()

# #         return [_format_asset(asset, query) for asset in assets]


# # def _format_asset(asset: Asset, query: str) -> dict:
# #     """
# #     Formats a PostgreSQL Asset into a result dict with a keyword_score.

# #     keyword_score is based on how many query terms matched — normalized to 0-1.
# #     """
# #     m          = asset.asset_metadata or {}
# #     mandatory  = m.get("mandatory")     or {}
# #     business   = m.get("business")      or {}
# #     content    = m.get("content")       or {}
# #     ai         = m.get("ai_enrichment") or {}

# #     # Score: count how many terms appear in asset_name + tags
# #     terms      = [t.lower() for t in query.split() if t.strip()]
# #     searchable = " ".join([
# #         mandatory.get("asset_name", ""),
# #         mandatory.get("description", ""),
# #         str(ai.get("ai_tags", "")),
# #         str(ai.get("searchable_tags", "")),
# #         str(content.get("keywords", "")),
# #     ]).lower()

# #     matched    = sum(1 for t in terms if t in searchable)
# #     score      = round(matched / max(len(terms), 1), 4)

# #     return {
# #         "asset_id":      str(asset.id),
# #         "keyword_score": score,
# #         "asset_name":    mandatory.get("asset_name", ""),
# #         "asset_type":    mandatory.get("asset_type", ""),
# #         "description":   mandatory.get("description", ""),
# #         "domain":        business.get("domain", ""),
# #         "use_case":      business.get("use_case", ""),
# #         "audience":      business.get("audience", ""),
# #         "funnel_stage":  business.get("funnel_stage", ""),
# #         "tone":          content.get("tone", ""),
# #         "owner":         mandatory.get("owner", ""),
# #         "status":        asset.status,
# #         "ai_tags":       ai.get("ai_tags") or [],
# #         "image_caption": ai.get("image_caption") or "",
# #         "original_filename": asset.original_filename,
# #     }

# # keyword_search_service.py
# # Keyword search against PostgreSQL JSONB asset_metadata.
# #
# # Searches across all metadata fields and returns full asset data.

# from sqlalchemy.orm import Session
# from sqlalchemy import or_, cast, String

# from app.models.asset.asset_model import Asset


# def _ilike(field, term: str):
#     return field.ilike(f"%{term}%")


# def _jsonb_ilike(column, *keys, term: str):
#     field = column
#     for key in keys:
#         field = field[key]
#     return cast(field, String).ilike(f"%{term}%")


# def _jsonb_array_ilike(column, *keys, term: str):
#     field = column
#     for key in keys:
#         field = field[key]
#     return cast(field, String).ilike(f"%{term}%")


# class KeywordSearchService:

#     @staticmethod
#     def search(
#         query: str,
#         db: Session,
#         limit: int = 20,
#         approved_only: bool = True,
#     ) -> list[dict]:

#         terms = [t.strip() for t in query.split() if t.strip()]
#         if not terms:
#             return []

#         base_query = db.query(Asset).filter(Asset.is_latest == True)

#         if approved_only:
#             base_query = base_query.filter(Asset.status == "approved")

#         for term in terms:
#             m = Asset.asset_metadata

#             term_filter = or_(
#                 _ilike(Asset.id, term),
#                 _ilike(Asset.original_filename, term),
#                 _ilike(Asset.mime_type, term),

#                 _jsonb_ilike(m, "mandatory", "asset_name",   term=term),
#                 _jsonb_ilike(m, "mandatory", "description",  term=term),
#                 _jsonb_ilike(m, "mandatory", "asset_type",   term=term),
#                 _jsonb_ilike(m, "mandatory", "owner",        term=term),
#                 _jsonb_ilike(m, "mandatory", "created_by",   term=term),
#                 _jsonb_ilike(m, "mandatory", "usage_rights", term=term),

#                 _jsonb_ilike(m, "business", "domain",       term=term),
#                 _jsonb_ilike(m, "business", "use_case",     term=term),
#                 _jsonb_ilike(m, "business", "audience",     term=term),
#                 _jsonb_ilike(m, "business", "funnel_stage", term=term),

#                 _jsonb_ilike(m, "content", "tone",                    term=term),
#                 _jsonb_array_ilike(m, "content", "keywords",          term=term),
#                 _jsonb_array_ilike(m, "content", "visual_elements",   term=term),

#                 _jsonb_array_ilike(m, "ai_enrichment", "ai_tags",         term=term),
#                 _jsonb_array_ilike(m, "ai_enrichment", "searchable_tags", term=term),
#                 _jsonb_ilike(m, "ai_enrichment", "extracted_text",        term=term),
#                 _jsonb_ilike(m, "ai_enrichment", "image_caption",         term=term),
#             )

#             base_query = base_query.filter(term_filter)

#         assets = base_query.limit(limit).all()

#         return [_format_asset(asset, query) for asset in assets]


# def _keyword_score(asset: Asset, query: str) -> float:
#     """Score based on how many query terms appear in key fields."""
#     m   = asset.asset_metadata or {}
#     ai  = m.get("ai_enrichment") or {}
#     man = m.get("mandatory") or {}
#     con = m.get("content") or {}

#     searchable = " ".join([
#         man.get("asset_name", ""),
#         man.get("description", ""),
#         str(ai.get("ai_tags", "")),
#         str(ai.get("searchable_tags", "")),
#         str(con.get("keywords", "")),
#     ]).lower()

#     terms   = [t.lower() for t in query.split() if t.strip()]
#     matched = sum(1 for t in terms if t in searchable)
#     return round(matched / max(len(terms), 1), 4)


# def _format_asset(asset: Asset, query: str) -> dict:
#     return {
#         "asset_id":          str(asset.id),
#         "keyword_score":     _keyword_score(asset, query),
#         "original_filename": asset.original_filename,
#         "storage_path":      asset.storage_path or "",
#         "thumbnail_path":    asset.thumbnail_path,
#         "preview_path":      asset.preview_path,
#         "mime_type":         asset.mime_type or "",
#         "status":            asset.status,
#         "asset_metadata":    asset.asset_metadata or {},
#     }
# app/ai/retrieval/keyword_search_service.py
# Keyword search against PostgreSQL JSONB asset_metadata.

from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String

from app.models.asset.asset_model import Asset


def _ilike(field, term: str):
    return field.ilike(f"%{term}%")


def _jsonb_ilike(column, *keys, term: str):
    field = column
    for key in keys:
        field = field[key]
    return cast(field, String).ilike(f"%{term}%")


class KeywordSearchService:

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 20,
        approved_only: bool = True,
    ) -> list[dict]:

        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []

        base_query = db.query(Asset).filter(Asset.is_latest == True)

        if approved_only:
            base_query = base_query.filter(Asset.status == "approved")

        for term in terms:
            m = Asset.asset_metadata

            base_query = base_query.filter(or_(
                _ilike(Asset.id, term),
                _ilike(Asset.original_filename, term),
                _ilike(Asset.mime_type, term),

                _jsonb_ilike(m, "mandatory", "asset_name",   term=term),
                _jsonb_ilike(m, "mandatory", "description",  term=term),
                _jsonb_ilike(m, "mandatory", "asset_type",   term=term),
                _jsonb_ilike(m, "mandatory", "owner",        term=term),
                _jsonb_ilike(m, "mandatory", "created_by",   term=term),
                _jsonb_ilike(m, "mandatory", "usage_rights", term=term),

                _jsonb_ilike(m, "business", "domain",        term=term),
                _jsonb_ilike(m, "business", "use_case",      term=term),
                _jsonb_ilike(m, "business", "audience",      term=term),
                _jsonb_ilike(m, "business", "funnel_stage",  term=term),

                _jsonb_ilike(m, "content", "tone",           term=term),
                _jsonb_ilike(m, "content", "keywords",       term=term),
                _jsonb_ilike(m, "content", "visual_elements", term=term),

                _jsonb_ilike(m, "ai_enrichment", "ai_tags",          term=term),
                _jsonb_ilike(m, "ai_enrichment", "searchable_tags",  term=term),
                _jsonb_ilike(m, "ai_enrichment", "extracted_text",   term=term),
                _jsonb_ilike(m, "ai_enrichment", "image_caption",    term=term),
            ))

        assets = base_query.limit(limit).all()
        return [_format_asset(asset, query) for asset in assets]


def _keyword_score(asset: Asset, query: str) -> float:
    m   = asset.asset_metadata or {}
    ai  = m.get("ai_enrichment") or {}
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

    terms   = [t.lower() for t in query.split() if t.strip()]
    matched = sum(1 for t in terms if t in searchable)
    return round(matched / max(len(terms), 1), 4)


def _format_asset(asset: Asset, query: str) -> dict:
    return {
        "asset_id":          str(asset.id),
        "keyword_score":     _keyword_score(asset, query),
        "original_filename": asset.original_filename or "",
        "storage_path":      asset.storage_path or "",
        "thumbnail_path":    asset.thumbnail_path,
        "preview_path":      asset.preview_path,
        "mime_type":         asset.mime_type or "",
        "status":            asset.status,
        "asset_metadata":    asset.asset_metadata or {},
    }