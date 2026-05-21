
# test_semantic_search.py
# Manual end-to-end test for the semantic search pipeline.
#
# Run from your backend root:
#   python test_semantic_search.py
#
# Tests:
#   1. build_semantic_document()  — correct text output
#   2. generate_embedding()       — correct vector shape
#   3. VectorUpsertService        — stores in ChromaDB without errors
#   4. SemanticSearchService      — returns ranked results
#   5. Filters                    — approved_only and metadata filters
#   6. Reindex                    — overwrites existing vector correctly

import sys
import os

# Allow running from backend root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.embeddings.embedding_utils import (
    build_semantic_document,
    generate_embedding,
    embed_asset,
)
from app.ai.embeddings.semantic_search_service import SemanticSearchService


# ---------------------------------------------------------------------------
# Fixtures — two sample assets mirroring AssetMetadataSchema
# ---------------------------------------------------------------------------

ASSET_BANNER = {
    "mandatory": {
        "asset_name": "AI Hero Banner v2",
        "asset_type": "banner",
        "description": "Homepage hero banner for AI services targeting enterprise clients",
        "created_by": "design_team",
        "usage_rights": "internal",
        "owner": "marketing",
    },
    "business": {
        "domain": "ai_services",
        "use_case": "website",
        "audience": "enterprise",
        "funnel_stage": "awareness",
    },
    "content": {
        "keywords": ["AI", "enterprise", "hero", "homepage", "banner"],
        "visual_elements": ["abstract", "blue gradient", "text overlay"],
        "tone": "professional",
    },
    "ai_enrichment": {
        "ai_tags": ["hero banner", "AI services", "enterprise", "homepage"],
        "searchable_tags": ["homepage banner", "enterprise AI", "landing page"],
        "detected_objects": ["text", "gradient", "logo"],
        "image_caption": "A professional banner showing AI solutions for enterprise",
        "extracted_text": "Transform your business with AI",
        "enrichment_status": "completed",
    },
}

ASSET_BROCHURE = {
    "mandatory": {
        "asset_name": "AI Staffing Case Study 2024",
        "asset_type": "document",
        "description": "Case study showing AI-driven staffing ROI for startup clients",
        "created_by": "content_team",
        "usage_rights": "external",
        "owner": "sales",
    },
    "business": {
        "domain": "staffing",
        "use_case": "sales",
        "audience": "startup",
        "funnel_stage": "consideration",
    },
    "content": {
        "keywords": ["staffing", "ROI", "case study", "startup", "AI"],
        "visual_elements": ["charts", "statistics", "logo"],
        "tone": "technical",
    },
    "ai_enrichment": {
        "ai_tags": ["case study", "staffing", "ROI", "startup"],
        "searchable_tags": ["staffing case study", "AI hiring", "startup ROI"],
        "detected_objects": ["text", "charts", "table"],
        "image_caption": None,
        "extracted_text": "Achieved 40% reduction in hiring time using AI matching",
        "enrichment_status": "completed",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg: str):
    print(f"  ✓  {msg}")

def fail(msg: str):
    print(f"  ✗  {msg}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# TEST 1 — build_semantic_document
# ---------------------------------------------------------------------------

section("TEST 1 — build_semantic_document()")

doc = build_semantic_document(ASSET_BANNER)

assert "AI Hero Banner v2" in doc,       "asset_name missing"
assert "enterprise" in doc,              "audience missing"
assert "ai_services" in doc,             "domain missing"
assert "homepage banner" in doc,         "searchable_tags missing"
assert "Transform your business" in doc, "extracted_text missing"

# Empty fields should not produce trailing colon lines
for line in doc.split("\n"):
    assert not line.endswith(": "), f"Empty field leaked into document: '{line}'"

ok("Document built correctly")
print(f"\n  --- Preview (first 400 chars) ---")
print(f"  {doc[:400].replace(chr(10), chr(10)+'  ')}")


# ---------------------------------------------------------------------------
# TEST 2 — generate_embedding
# ---------------------------------------------------------------------------

section("TEST 2 — generate_embedding()")

embedding = generate_embedding("AI landing page banner for enterprise clients")

assert isinstance(embedding, list),         "embedding must be a list"
assert len(embedding) == 384,               "all-MiniLM-L6-v2 produces 384-dim vectors"
assert all(isinstance(v, float) for v in embedding), "all values must be floats"

ok(f"Embedding shape: {len(embedding)} dimensions")
ok(f"Sample values: {embedding[:4]}")


# ---------------------------------------------------------------------------
# TEST 3 — index_asset (upsert into ChromaDB)
# ---------------------------------------------------------------------------

section("TEST 3 — SemanticSearchService.index_asset()")

result = SemanticSearchService.index_asset(
    asset_id="test-banner-001",
    asset=ASSET_BANNER,
    status="approved",
)
assert result is True, "index_asset should return True"
ok("Indexed ASSET_BANNER (test-banner-001)")

result = SemanticSearchService.index_asset(
    asset_id="test-brochure-001",
    asset=ASSET_BROCHURE,
    status="approved",
)
assert result is True, "index_asset should return True"
ok("Indexed ASSET_BROCHURE (test-brochure-001)")

# Index a draft asset — should NOT appear in approved_only search
draft_asset = dict(ASSET_BANNER)
draft_asset["mandatory"] = {**ASSET_BANNER["mandatory"], "asset_name": "Draft Banner WIP"}
SemanticSearchService.index_asset(
    asset_id="test-draft-001",
    asset=draft_asset,
    status="draft",
)
ok("Indexed DRAFT asset (test-draft-001)")


# ---------------------------------------------------------------------------
# TEST 4 — semantic_search (approved only, no filters)
# ---------------------------------------------------------------------------

section("TEST 4 — SemanticSearchService.search() — approved only")

results = SemanticSearchService.search(
    query="AI landing page banner for enterprise clients",
    limit=5,
    approved_only=True,
)

assert len(results) >= 1,                            "should return at least 1 result"
assert results[0]["asset_id"] == "test-banner-001",  "banner should rank first"
assert results[0]["score"] > 0.5,                    "score should be reasonably high"

# Draft should NOT appear
ids = [r["asset_id"] for r in results]
assert "test-draft-001" not in ids, "draft asset must not appear in approved_only search"

ok(f"Returned {len(results)} results")
for r in results:
    print(f"     [{r['score']:.2f}] {r['asset_name']} ({r['asset_id']})")


# ---------------------------------------------------------------------------
# TEST 5 — filters (asset_type)
# ---------------------------------------------------------------------------

section("TEST 5 — Filters: asset_type=document")

results = SemanticSearchService.search(
    query="staffing case study startup ROI",
    limit=5,
    approved_only=True,
    filters={"asset_type": "document"},
)

assert len(results) >= 1,                              "should return at least 1 result"
assert results[0]["asset_id"] == "test-brochure-001",  "brochure should rank first"
assert all(r["asset_type"] == "document" for r in results), "all results must be documents"

ok(f"Filter works — {len(results)} document(s) returned")
for r in results:
    print(f"     [{r['score']:.2f}] {r['asset_name']} (type: {r['asset_type']})")


# ---------------------------------------------------------------------------
# TEST 6 — reindex (overwrite)
# ---------------------------------------------------------------------------

section("TEST 6 — reindex_asset() — overwrite vector")

updated_banner = dict(ASSET_BANNER)
updated_banner["mandatory"] = {
    **ASSET_BANNER["mandatory"],
    "asset_name": "AI Hero Banner v3 (Updated)",
}

result = SemanticSearchService.reindex_asset(
    asset_id="test-banner-001",
    asset=updated_banner,
    status="approved",
)
assert result is True, "reindex_asset should return True"
ok("Reindex successful — same ID, updated content")

# Verify updated name is retrievable
results = SemanticSearchService.search(
    query="AI hero banner enterprise",
    limit=3,
    approved_only=True,
)
assert any(r["asset_id"] == "test-banner-001" for r in results), \
    "Reindexed asset should still be retrievable"
ok("Reindexed asset is retrievable in search")


# ---------------------------------------------------------------------------
# DONE
# ---------------------------------------------------------------------------

section("ALL TESTS PASSED ✓")
print()
print("  Semantic search pipeline is working correctly.")
print("  You can now wire search_route.py into your FastAPI app.")
print()