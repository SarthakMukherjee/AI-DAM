from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import require_admin
from app.models.user.user_model import User
from app.models.taxonomy.taxonomy_model import Category, Tag
from app.models.asset.asset_model import Asset
from app.ai.retrieval.semantic_search_service import SemanticSearchService
from sqlalchemy import cast, String
from app.schemas.taxonomy.taxonomy_schema import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    TagCreate, TagUpdate, TagResponse, TagMergeRequest
)

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])

# --- Categories ---

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_cat = Category(**category.model_dump())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    for key, value in category_in.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
        
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db.delete(cat)
    db.commit()
    return {"message": "Category deleted"}


# --- Tags ---

@router.get("/tags", response_model=List[TagResponse])
def list_tags(category_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Tag)
    if category_id:
        query = query.filter(Tag.category_id == category_id)
    return query.order_by(Tag.name).all()

@router.post("/tags", response_model=TagResponse)
def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    cat = db.query(Category).filter(Category.id == tag.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    existing = db.query(Tag).filter(Tag.name == tag.name, Tag.category_id == tag.category_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists in this category")
        
    new_tag = Tag(**tag.model_dump())
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@router.put("/tags/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: str,
    tag_in: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    if tag_in.category_id and tag_in.category_id != tag.category_id:
        cat = db.query(Category).filter(Category.id == tag_in.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="New category not found")
            
    for key, value in tag_in.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
        
    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}

@router.post("/tags/merge", response_model=TagResponse)
def merge_tags(
    payload: TagMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    source_tag = db.query(Tag).filter(Tag.id == payload.source_tag_id).first()
    target_tag = db.query(Tag).filter(Tag.id == payload.target_tag_id).first()
    
    if not source_tag or not target_tag:
        raise HTTPException(status_code=404, detail="One or both tags not found")
        
    if source_tag.category_id != target_tag.category_id:
        raise HTTPException(status_code=400, detail="Tags must belong to the same category to be merged")
        
    # Append source tag name to target tag synonyms
    synonyms = target_tag.synonyms or []
    if source_tag.name not in synonyms and source_tag.name != target_tag.name:
        synonyms.append(source_tag.name)
        
    # also add source_tag synonyms to target_tag synonyms
    if source_tag.synonyms:
        for syn in source_tag.synonyms:
            if syn not in synonyms and syn != target_tag.name:
                synonyms.append(syn)
                
    target_tag.synonyms = list(set(synonyms))
    
    # Now find all assets having the source_tag in ai_tags
    # ai_tags is a JSONB list, we can just do string contains for simplicity in POC
    assets = db.query(Asset).filter(cast(Asset.ai_tags, String).ilike(f'%"{source_tag.name}"%')).all()
    
    for asset in assets:
        if asset.ai_tags:
            new_tags = []
            for t in asset.ai_tags:
                if t == source_tag.name:
                    if target_tag.name not in asset.ai_tags:
                        new_tags.append(target_tag.name)
                else:
                    new_tags.append(t)
            asset.ai_tags = list(set(new_tags))
            
        # Update asset_metadata.ai_enrichment.ai_tags if exists
        meta = asset.asset_metadata or {}
        ai_enrich = meta.get("ai_enrichment", {})
        if ai_enrich:
            ai_tags = ai_enrich.get("ai_tags", [])
            if ai_tags:
                new_tags = []
                for t in ai_tags:
                    if t == source_tag.name:
                        if target_tag.name not in ai_tags:
                            new_tags.append(target_tag.name)
                    else:
                        new_tags.append(t)
                ai_enrich["ai_tags"] = list(set(new_tags))
                meta["ai_enrichment"] = ai_enrich
                asset.asset_metadata = meta
    
    # Delete source tag
    db.delete(source_tag)
    db.commit()
    
    # Reindex updated assets
    for asset in assets:
        SemanticSearchService.reindex_asset(
            asset_id=asset.id,
            asset_metadata=asset.asset_metadata,
            status=asset.status
        )
        
    db.refresh(target_tag)
    return target_tag
