from app.ai.embeddings.embedding_utils import (
    build_semantic_document
    )

test_asset = { 
    "original_filename": "marketing banner 123.jpg",
    "mime_type": "image/jpeg",
    "id": "c67647c2-a1d8-41b9-867a-39347988dbab",

    "asset_metadata": {

        "content": {
            "tone": "professional",
            "keywords": [
                "AI",
                "dashboard"
            ],
            "visual_elements": [
                "charts",
                "UI"
            ]
        },

        "business": {
            "domain": "AI",
            "audience": "enterprise",
            "use_case": "website",
            "funnel_stage": "awareness"
        },

        "mandatory": {
            "owner": "marketing",
            "asset_name": "Marketing Banner",
            "asset_type": "image",
            "created_by": "John",
            "description": "Company marketing hero banner",
            "usage_rights": "internal"
        },

        "ai_enrichment": {
            "ai_tags": [
                "marketing",
                "icons"
            ],
            "image_caption": (
                "marketing word with icons and icons"
            ),
            "extracted_text": "",
            "searchable_tags": [
                "marketing",
                "icons"
            ],
            "detected_objects": [],
            "enrichment_status": "completed"
        }}}

result = build_semantic_document(test_asset)
print("FINAL OUTPUT:\n", result)
