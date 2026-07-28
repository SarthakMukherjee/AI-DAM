import sys
import os
import uuid
from datetime import datetime, timezone
sys.path.append(os.path.join(os.getcwd(), 'app'))

from app.db.session.database import SessionLocal
from app.models.asset.asset_model import Asset
from app.models.analytics.asset_usage_model import AssetUsage
from app.ai.retrieval.semantic_search_service import SemanticSearchService
from app.ai.vectorstore.vector_upsert_service import VectorUpsertService

db = SessionLocal()
try:
    # 1. Create a dummy asset
    asset_id = str(uuid.uuid4())
    dummy = Asset(
        id=asset_id,
        original_filename="dummy.jpg",
        stored_filename="dummy.jpg",
        file_hash="dummy_hash",
        status="approved",
        completeness_score=85,
        created_at=datetime.now(timezone.utc),
        is_latest=True
    )
    db.add(dummy)
    db.commit()
    
    # 2. Add some usage
    usage = AssetUsage(
        asset_id=asset_id,
        action="download",
        usage_count=50
    )
    db.add(usage)
    db.commit()
    
    # 3. Index it in Chroma
    SemanticSearchService.index_asset(
        asset_id=asset_id,
        asset_metadata={"mandatory": {"description": "A beautiful sunset test dummy asset"}},
        status="approved"
    )

    # 4. Search for it
    results = SemanticSearchService.search(query='sunset', db=db, limit=5, approved_only=False)
    print('Found results:', len(results))
    if results:
        for r in results:
            print(f"Asset ID: {r['asset_id']}, Score: {r['score']}")
            print(f"Breakdown: {r['ranking_breakdown']}")

    # 5. Cleanup
    db.delete(usage)
    db.delete(dummy)
    db.commit()
finally:
    db.close()
