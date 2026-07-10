from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagBase(BaseModel):
    name: str
    category_id: str
    synonyms: Optional[List[str]] = []
    is_active: Optional[bool] = True

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    synonyms: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TagResponse(TagBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
