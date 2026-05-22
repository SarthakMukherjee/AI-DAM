# # # Stores semantic embeddings

# # from app.ai.vectorstore.vector_collection_service import (
# #     VectorCollectionService
# # )

# # class VectorUpsertService:

# #     @staticmethod
# #     def upsert_embedding(
# #         asset_id: str,
# #         embedding: list,
# #         document: str,
# #         metadata: dict
# #     ):
        
# #         collection = VectorCollectionService.get_collection()

# #         collection.upsert(
# #             ids=[asset_id],
# #             embeddings=[embedding],
# #             documents=[document],
# #             metadatas=[metadata]
# #         )

# #         return True

# # vector_upsert_service.py
# # Stores semantic embeddings + metadata in ChromaDB.
# #
# # IMPORTANT — ChromaDB metadata constraint:
# # Chroma only accepts flat dicts with str | int | float | bool values.
# # Lists, nested dicts, and None are NOT allowed.
# # _flatten_metadata() handles this before every upsert.

from app.ai.vectorstore.vector_collection_service import VectorCollectionService


def _flatten_metadata(asset_id: str, asset: dict) -> dict:
    """
    Converts the full nested asset dict into a flat ChromaDB-safe dict.

    Lists  → joined as comma-separated strings
    None   → empty string ""
    Enums  → their .value (string)
    Nested → prefixed keys (e.g. "business_domain")

    Only stores fields useful for post-search filtering — not the full
    semantic document (that's stored in the `documents` field of Chroma).
    """
    mandatory = asset.get("mandatory", {})
    business  = asset.get("business", {})
    content   = asset.get("content", {})
    ai        = asset.get("ai_enrichment") or {}

    def s(d, key):
        """Safely get a scalar string value, unwrapping enums."""
        v = d.get(key, "")
        if v is None:
            return ""
        return v.value if hasattr(v, "value") else str(v)

    def lst(d, key):
        """Safely join a list field into a comma-separated string."""
        items = d.get(key) or []
        return ", ".join(str(i) for i in items if i)

    return {
        # --- identity ---
        "asset_id":       asset_id,
        "asset_name":     s(mandatory, "asset_name"),
        "asset_type":     s(mandatory, "asset_type"),
        "owner":          s(mandatory, "owner"),
        "created_by":     s(mandatory, "created_by"),
        "usage_rights":   s(mandatory, "usage_rights"),

        # --- business (filterable) ---
        "domain":         s(business, "domain"),
        "use_case":       s(business, "use_case"),
        "audience":       s(business, "audience"),
        "funnel_stage":   s(business, "funnel_stage"),

        # --- content (searchable signals, stored as strings) ---
        "tone":           s(content, "tone"),
        "keywords":       lst(content, "keywords"),
        "visual_elements": lst(content, "visual_elements"),

        # --- ai enrichment ---
        "ai_tags":           lst(ai, "ai_tags"),
        "searchable_tags":   lst(ai, "searchable_tags"),
        "detected_objects":  lst(ai, "detected_objects"),
        "image_caption":     ai.get("image_caption") or "",
        "enrichment_status": ai.get("enrichment_status") or "",
    }


class VectorUpsertService:

    @staticmethod
    def upsert_asset(
        asset_id: str,
        asset: dict,
        status: str = "approved",
    ) -> bool:
        """
        Full upsert: takes the raw asset dict, builds flat metadata,
        and stores embedding + document + metadata in ChromaDB.

        Args:
            asset_id:  The DB asset UUID (used as Chroma document ID)
            asset:     The full asset dict (mandatory/business/content/ai_enrichment)
            status:    Asset lifecycle status — stored for filtering

        Requires:
            Call embed_asset(asset) before this to get document + embedding.
        """
        raise NotImplementedError(
            "Call upsert_embedding() directly with pre-computed embedding, "
            "or use SemanticSearchService.index_asset() which handles both."
        )

    @staticmethod
    def upsert_embedding(
        asset_id: str,
        embedding: list,
        document: str,
        asset: dict,
        status: str = "approved",
    ) -> bool:
        """
        Stores a pre-computed embedding in ChromaDB.

        Args:
            asset_id:   Chroma document ID (your DB asset UUID)
            embedding:  Vector from generate_embedding()
            document:   Semantic text from build_semantic_document()
            asset:      Full asset dict — used to build flat metadata
            status:     Asset lifecycle status (stored for where-filtering)

        Returns:
            True on success.
        """
        collection = VectorCollectionService.get_collection()

        metadata = _flatten_metadata(asset_id, asset)
        metadata["status"] = status  # add lifecycle status for filtering

        collection.upsert(
            ids=[asset_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

        return True
    






    
# vector_upsert_service.py
# Stores semantic embeddings + metadata in ChromaDB.
#
# IMPORTANT — ChromaDB metadata constraint:
# Chroma only accepts flat dicts with str | int | float | bool values.
# Lists, nested dicts, and None are NOT allowed.
# _flatten_metadata() handles this before every upsert.

from app.ai.vectorstore.vector_collection_service import VectorCollectionService


def _flatten_metadata(asset_id: str, asset: dict) -> dict:
    """
    Converts the full nested asset dict into a flat ChromaDB-safe dict.

    Lists  → joined as comma-separated strings
    None   → empty string ""
    Enums  → their .value (string)
    Nested → prefixed keys (e.g. "business_domain")

    Only stores fields useful for post-search filtering — not the full
    semantic document (that's stored in the `documents` field of Chroma).
    """
    mandatory = asset.get("mandatory", {})
    business  = asset.get("business", {})
    content   = asset.get("content", {})
    ai        = asset.get("ai_enrichment") or {}

    def s(d, key):
        """Safely get a scalar string value, unwrapping enums."""
        v = d.get(key, "")
        if v is None:
            return ""
        return v.value if hasattr(v, "value") else str(v)

    def lst(d, key):
        """Safely join a list field into a comma-separated string."""
        items = d.get(key) or []
        return ", ".join(str(i) for i in items if i)

    return {
        # --- identity ---
        "asset_id":       asset_id,
        "asset_name":     s(mandatory, "asset_name"),
        "asset_type":     s(mandatory, "asset_type"),
        "owner":          s(mandatory, "owner"),
        "created_by":     s(mandatory, "created_by"),
        "usage_rights":   s(mandatory, "usage_rights"),

        # --- business (filterable) ---
        "domain":         s(business, "domain"),
        "use_case":       s(business, "use_case"),
        "audience":       s(business, "audience"),
        "funnel_stage":   s(business, "funnel_stage"),

        # --- content (searchable signals, stored as strings) ---
        "tone":           s(content, "tone"),
        "keywords":       lst(content, "keywords"),
        "visual_elements": lst(content, "visual_elements"),

        # --- ai enrichment ---
        "ai_tags":           lst(ai, "ai_tags"),
        "searchable_tags":   lst(ai, "searchable_tags"),
        "detected_objects":  lst(ai, "detected_objects"),
        "image_caption":     ai.get("image_caption") or "",
        "enrichment_status": ai.get("enrichment_status") or "",
    }


class VectorUpsertService:

    @staticmethod
    def upsert_asset(
        asset_id: str,
        asset: dict,
        status: str = "approved",
    ) -> bool:
        """
        Full upsert: takes the raw asset dict, builds flat metadata,
        and stores embedding + document + metadata in ChromaDB.

        Args:
            asset_id:  The DB asset UUID (used as Chroma document ID)
            asset:     The full asset dict (mandatory/business/content/ai_enrichment)
            status:    Asset lifecycle status — stored for filtering

        Requires:
            Call embed_asset(asset) before this to get document + embedding.
        """
        raise NotImplementedError(
            "Call upsert_embedding() directly with pre-computed embedding, "
            "or use SemanticSearchService.index_asset() which handles both."
        )

    @staticmethod
    def upsert_embedding(
        asset_id: str,
        embedding: list,
        document: str,
        asset: dict,
        status: str = "approved",
    ) -> bool:
        """
        Stores a pre-computed embedding in ChromaDB.

        Args:
            asset_id:   Chroma document ID (your DB asset UUID)
            embedding:  Vector from generate_embedding()
            document:   Semantic text from build_semantic_document()
            asset:      Full asset dict — used to build flat metadata
            status:     Asset lifecycle status (stored for where-filtering)

        Returns:
            True on success.
        """
        collection = VectorCollectionService.get_collection()

        metadata = _flatten_metadata(asset_id, asset)
        metadata["status"] = status  # add lifecycle status for filtering

        collection.upsert(
            ids=[asset_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

        return True