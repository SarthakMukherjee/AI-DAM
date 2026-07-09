from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import require_admin
from app.models.user.user_model import User
from app.models.taxonomy.taxonomy_model import Category, Tag
from app.schemas.taxonomy.taxonomy_schema import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    TagCreate, TagUpdate, TagResponse
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
