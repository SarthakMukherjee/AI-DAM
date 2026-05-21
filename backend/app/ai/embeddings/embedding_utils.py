# # this file will:
# # Convert DAM metadata -> Semantic search document

# def build_semantic_document(asset: dict) -> str:

#     metadata = asset.get("asset_metadata") or {}
#     mandatory = asset.get("mandatory") or {}
#     business = asset.get("business") or {}
#     content = asset.get("content") or {}
#     ai = asset.get("ai_enrichment") or  {}

#     semantic_parts = []

#     semantic_parts.append(f"Asset Name: {mandatory.get('asset_name', '')}")

#     semantic_parts.append(f"Description: {mandatory.get('description', '')}")

#     semantic_parts.append(f"Asset Type: {mandatory.get('asset_type', '')}")

#     semantic_parts.append(f"Business Domain: {business.get('domain', '')}")

#     semantic_parts.append(f"Audience: {business.get('audience', '')}")

#     semantic_parts.append(f"Use Case: {business.get('use_case', '')}")

#     semantic_parts.append(f"Funnel Stage: {business.get('funnel_stage', '')}")

#     semantic_parts.append(f"Tone: {content.get('tone', '')}")

#     keywords = content.get("keywords", [])

#     semantic_parts.append(f"Keywords: {', '.join(keywords)}")

#     visual_elements = content.get("visual_elements", [])

#     semantic_parts.append(f"Visual Elements: {', '.join(visual_elements)}")

#     semantic_parts.append(f"Image Caption: {ai.get('image_caption', '')}")

#     semantic_parts.append(f"Extracted Text: {ai.get('extracted_text', '')}")

#     ai_tags = ai.get("ai_tags", [])

#     semantic_parts.append(f"AI Tags: {', '.join(ai_tags)}")

#     detected_objects = ai.get("detected_objects", [])

#     semantic_parts.append(f"Detected Objects: {'. '.join(detected_objects)}")

#     semantic_document = "\n".join(semantic_parts)

#     return semantic_document



def build_semantic_document(asset: dict) -> str:

    # MAIN METADATA
    metadata = asset.get("asset_metadata") or {}

    # SUB-METADATA
    mandatory = metadata.get("mandatory") or {}
    business = metadata.get("business") or {}
    content = metadata.get("content") or {}
    ai = metadata.get("ai_enrichment") or {}

    semantic_parts = []

    # Mandatory Metadata
    semantic_parts.append(
        f"Asset Name: {mandatory.get('asset_name', '')}"
    )

    semantic_parts.append(
        f"Description: {mandatory.get('description', '')}"
    )

    semantic_parts.append(
        f"Asset Type: {mandatory.get('asset_type', '')}"
    )

    # Business Metadata
    semantic_parts.append(
        f"Business Domain: {business.get('domain', '')}"
    )

    semantic_parts.append(
        f"Audience: {business.get('audience', '')}"
    )

    semantic_parts.append(
        f"Use Case: {business.get('use_case', '')}"
    )

    semantic_parts.append(
        f"Funnel Stage: {business.get('funnel_stage', '')}"
    )

    # Content Metadata
    semantic_parts.append(
        f"Tone: {content.get('tone', '')}"
    )

    keywords = content.get("keywords") or []

    semantic_parts.append(
        f"Keywords: {', '.join(keywords)}"
    )

    visual_elements = (
        content.get("visual_elements") or []
    )

    semantic_parts.append(
        f"Visual Elements: {', '.join(visual_elements)}"
    )

    # AI Enrichment
    semantic_parts.append(
        f"Image Caption: {ai.get('image_caption', '')}"
    )

    semantic_parts.append(
        f"Extracted Text: {ai.get('extracted_text', '')}"
    )

    ai_tags = ai.get("ai_tags") or []

    semantic_parts.append(
        f"AI Tags: {', '.join(ai_tags)}"
    )

    detected_objects = (
        ai.get("detected_objects") or []
    )

    semantic_parts.append(
        f"Detected Objects: {', '.join(detected_objects)}"
    )

    semantic_document = "\n".join(semantic_parts)

    return semantic_document