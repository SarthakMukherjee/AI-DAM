# # # this file will:
# # # Convert DAM metadata -> Semantic search document

# # def build_semantic_document(asset: dict) -> str:

# #     metadata = asset.get("asset_metadata") or {}
# #     mandatory = asset.get("mandatory") or {}
# #     business = asset.get("business") or {}
# #     content = asset.get("content") or {}
# #     ai = asset.get("ai_enrichment") or  {}

# #     semantic_parts = []

# #     semantic_parts.append(f"Asset Name: {mandatory.get('asset_name', '')}")

# #     semantic_parts.append(f"Description: {mandatory.get('description', '')}")

# #     semantic_parts.append(f"Asset Type: {mandatory.get('asset_type', '')}")

# #     semantic_parts.append(f"Business Domain: {business.get('domain', '')}")

# #     semantic_parts.append(f"Audience: {business.get('audience', '')}")

# #     semantic_parts.append(f"Use Case: {business.get('use_case', '')}")

# #     semantic_parts.append(f"Funnel Stage: {business.get('funnel_stage', '')}")

# #     semantic_parts.append(f"Tone: {content.get('tone', '')}")

# #     keywords = content.get("keywords", [])

# #     semantic_parts.append(f"Keywords: {', '.join(keywords)}")

# #     visual_elements = content.get("visual_elements", [])

# #     semantic_parts.append(f"Visual Elements: {', '.join(visual_elements)}")

# #     semantic_parts.append(f"Image Caption: {ai.get('image_caption', '')}")

# #     semantic_parts.append(f"Extracted Text: {ai.get('extracted_text', '')}")

# #     ai_tags = ai.get("ai_tags", [])

# #     semantic_parts.append(f"AI Tags: {', '.join(ai_tags)}")

# #     detected_objects = ai.get("detected_objects", [])

# #     semantic_parts.append(f"Detected Objects: {'. '.join(detected_objects)}")

# #     semantic_document = "\n".join(semantic_parts)

# #     return semantic_document



# def build_semantic_document(asset: dict) -> str:

#     # MAIN METADATA
#     metadata = asset.get("asset_metadata") or {}

#     # SUB-METADATA
#     mandatory = metadata.get("mandatory") or {}
#     business = metadata.get("business") or {}
#     content = metadata.get("content") or {}
#     ai = metadata.get("ai_enrichment") or {}

#     semantic_parts = []

#     # Mandatory Metadata
#     semantic_parts.append(
#         f"Asset Name: {mandatory.get('asset_name', '')}"
#     )

#     semantic_parts.append(
#         f"Description: {mandatory.get('description', '')}"
#     )

#     semantic_parts.append(
#         f"Asset Type: {mandatory.get('asset_type', '')}"
#     )

#     # Business Metadata
#     semantic_parts.append(
#         f"Business Domain: {business.get('domain', '')}"
#     )

#     semantic_parts.append(
#         f"Audience: {business.get('audience', '')}"
#     )

#     semantic_parts.append(
#         f"Use Case: {business.get('use_case', '')}"
#     )

#     semantic_parts.append(
#         f"Funnel Stage: {business.get('funnel_stage', '')}"
#     )

#     # Content Metadata
#     semantic_parts.append(
#         f"Tone: {content.get('tone', '')}"
#     )

#     keywords = content.get("keywords") or []

#     semantic_parts.append(
#         f"Keywords: {', '.join(keywords)}"
#     )

#     visual_elements = (
#         content.get("visual_elements") or []
#     )

#     semantic_parts.append(
#         f"Visual Elements: {', '.join(visual_elements)}"
#     )

#     # AI Enrichment
#     semantic_parts.append(
#         f"Image Caption: {ai.get('image_caption', '')}"
#     )

#     semantic_parts.append(
#         f"Extracted Text: {ai.get('extracted_text', '')}"
#     )

#     ai_tags = ai.get("ai_tags") or []

#     semantic_parts.append(
#         f"AI Tags: {', '.join(ai_tags)}"
#     )

#     detected_objects = (
#         ai.get("detected_objects") or []
#     )

#     semantic_parts.append(
#         f"Detected Objects: {', '.join(detected_objects)}"
#     )

#     semantic_document = "\n".join(semantic_parts)

#     return semantic_document
# embedding_utils.py
# Converts DAM asset_metadata dict -> semantic document string
# Generates sentence-transformer embeddings for vector storage
#
# asset_metadata structure (from PostgreSQL asset.asset_metadata):
# {
#     "mandatory":     { asset_name, asset_type, description, ... },
#     "business":      { domain, use_case, audience, funnel_stage },
#     "content":       { keywords: [], visual_elements: [], tone },
#     "ai_enrichment": { ai_tags: [], extracted_text, image_caption,
#                        detected_objects: [], searchable_tags: [] }
# }

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the model once and reuse across calls."""
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def build_semantic_document(asset_metadata: dict) -> str:
    """
    Converts asset_metadata dict into a single semantic text document.

    Accepts the direct asset_metadata dict (mandatory/business/content/ai_enrichment).
    This is what asset.asset_metadata returns from PostgreSQL.

    Usage:
        doc = build_semantic_document(asset.asset_metadata)
    """

    mandatory     = asset_metadata.get("mandatory")     or {}
    business      = asset_metadata.get("business")      or {}
    content       = asset_metadata.get("content")       or {}
    ai            = asset_metadata.get("ai_enrichment") or {}

    # --- helpers ---
    def val(d, key):
        """Safely get a string value; handles enums with .value."""
        v = d.get(key, "")
        if v is None:
            return ""
        return v.value if hasattr(v, "value") else str(v)

    def join(lst):
        """Safely join a list that may be None."""
        if not lst:
            return ""
        return ", ".join(str(v) for v in lst if v)

    # --- build parts in priority order ---
    parts = [
        # Core identity
        f"Asset Name: {val(mandatory, 'asset_name')}",
        f"Description: {val(mandatory, 'description')}",
        f"Asset Type: {val(mandatory, 'asset_type')}",

        # Business context
        f"Business Domain: {val(business, 'domain')}",
        f"Use Case: {val(business, 'use_case')}",
        f"Audience: {val(business, 'audience')}",
        f"Funnel Stage: {val(business, 'funnel_stage')}",

        # Content signals
        f"Tone: {val(content, 'tone')}",
        f"Keywords: {join(content.get('keywords'))}",
        f"Visual Elements: {join(content.get('visual_elements'))}",

        # AI-enriched signals
        f"AI Tags: {join(ai.get('ai_tags'))}",
        f"Searchable Tags: {join(ai.get('searchable_tags'))}",
        f"Detected Objects: {join(ai.get('detected_objects'))}",
        f"Image Caption: {ai.get('image_caption') or ''}",
        f"Extracted Text: {ai.get('extracted_text') or ''}",
    ]

    # Drop empty lines so they don't dilute the embedding
    document = "\n".join(p for p in parts if not p.endswith(": "))

    return document


def generate_embedding(text: str) -> list[float]:
    """
    Encodes a string into a vector using SentenceTransformers.
    Returns a plain Python list (ChromaDB expects list, not numpy array).
    """
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_asset(asset_metadata: dict) -> tuple[str, list[float]]:
    """
    Convenience: build document + embed in one call.

    Args:
        asset_metadata: the direct asset_metadata dict from PostgreSQL

    Returns:
        document  (str)         — semantic text (stored in Chroma)
        embedding (list[float]) — vector (stored in Chroma)

    Usage:
        doc, vec = embed_asset(asset.asset_metadata)
    """
    document  = build_semantic_document(asset_metadata)
    embedding = generate_embedding(document)
    return document, embedding