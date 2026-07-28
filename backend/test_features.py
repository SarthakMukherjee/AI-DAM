import sys
import os
import uuid
from datetime import datetime, timezone
sys.path.append(os.path.join(os.getcwd(), 'app'))

from fastapi import Request
from app.db.session.database import SessionLocal, Base, engine
from app.models.asset.asset_model import Asset
from app.models.taxonomy.taxonomy_model import Category, Tag
from app.models.user.user_model import User
from app.schemas.asset_schema import AssetBulkActionRequest, AssetBulkApproveRequest, AssetCommentCreate
from app.schemas.taxonomy.taxonomy_schema import TagMergeRequest
from app.api.routes.asset_routes import bulk_retire_assets, create_asset_comment
from app.api.routes.reviewer_routes import bulk_approve_assets
from app.api.routes.taxonomy_routes import merge_tags

# ensure tables exist
Base.metadata.create_all(bind=engine)

class MockRequest:
    class Client:
        host = "127.0.0.1"
    client = Client()

def run_tests():
    db = SessionLocal()
    try:
        # 1. Setup mock user
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@test.com",
            full_name="Admin",
            hashed_password="hash",
            role="super_admin",
            allowed_domains=[]
        )
        db.add(admin)
        
        # 2. Setup mock assets
        a1 = Asset(id=str(uuid.uuid4()), original_filename="a1.jpg", stored_filename="a1.jpg", status="draft", file_hash="hash1")
        a2 = Asset(id=str(uuid.uuid4()), original_filename="a2.jpg", stored_filename="a2.jpg", status="draft", file_hash="hash2")
        db.add(a1)
        db.add(a2)
        db.commit()

        print("[Point 6] Testing Bulk Approve...")
        approve_req = AssetBulkApproveRequest(asset_ids=[a1.id, a2.id], brand_aligned=True)
        res = bulk_approve_assets(payload=approve_req, request=MockRequest(), db=db, current_user=admin)
        print("Approve result:", res)
        db.refresh(a1)
        assert a1.status == "approved"
        
        print("[Point 6] Testing Bulk Retire...")
        retire_req = AssetBulkActionRequest(asset_ids=[a1.id, a2.id])
        res = bulk_retire_assets(payload=retire_req, request=MockRequest(), db=db, current_user=admin)
        print("Retire result:", res)
        db.refresh(a1)
        assert a1.status == "retired"

        print("[Point 7] Testing Collaboration...")
        comment_req = AssetCommentCreate(content="This is a test comment!")
        comment = create_asset_comment(asset_id=a1.id, payload=comment_req, db=db, current_user=admin)
        print("Created comment:", comment.content)

        print("[Point 9] Testing Taxonomy Merge...")
        cat = Category(id=str(uuid.uuid4()), name="Test Category")
        t1 = Tag(id=str(uuid.uuid4()), name="old_tag", category_id=cat.id)
        t2 = Tag(id=str(uuid.uuid4()), name="new_tag", category_id=cat.id)
        db.add(cat)
        db.add(t1)
        db.add(t2)
        
        # give a1 the old tag
        a1.ai_tags = ["old_tag", "other_tag"]
        a1.asset_metadata = {"ai_enrichment": {"ai_tags": ["old_tag"]}}
        db.commit()
        
        merge_req = TagMergeRequest(source_tag_id=t1.id, target_tag_id=t2.id)
        merged = merge_tags(payload=merge_req, db=db, current_user=admin)
        print("Merged tag synonyms:", merged.synonyms)
        assert "old_tag" in merged.synonyms
        
        db.refresh(a1)
        print("Asset updated tags:", a1.ai_tags)
        assert "new_tag" in a1.ai_tags
        assert "old_tag" not in a1.ai_tags
        
        print("All tests passed successfully!")
    except Exception as e:
        print("Test failed:", e)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
