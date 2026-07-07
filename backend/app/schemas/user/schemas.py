from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# -----------------------------------
# AUTH SCHEMAS
# -----------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -----------------------------------
# USER SCHEMAS
# -----------------------------------

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    allowed_domains: list[str] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateRoleRequest(BaseModel):
    role: str  # admin / reviewer / user / marketing_manager / etc.


class UpdateDomainsRequest(BaseModel):
    allowed_domains: list[str]  # e.g. ["Healthcare", "Finance"]


# -----------------------------------
# REVIEW SCHEMAS
# -----------------------------------

class ApproveRequest(BaseModel):
    website_safe: Optional[bool] = None
    public_use_approved: Optional[bool] = None
    brand_aligned: Optional[bool] = None

class ReviewRequest(BaseModel):
    reason: Optional[str] = None
    rejection_category: Optional[str] = None
    # rejection_category values: "quality", "brand", "legal", "outdated", "wrong_format", "other"


class PublishRequest(BaseModel):
    publish_note: Optional[str] = None
    published_channels: Optional[list[str]] = None  # e.g. ["web", "email"]


class RestrictRequest(BaseModel):
    reason: Optional[str] = None
    restricted_to_roles: Optional[list[str]] = None  # e.g. ["admin", "reviewer"]


# -----------------------------------
# NOTIFICATION SCHEMAS
# -----------------------------------

class NotificationResponse(BaseModel):
    id: str
    asset_id: str
    message: str
    reason: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------
# ANALYTICS SCHEMAS
# -----------------------------------

class AssetUsageResponse(BaseModel):
    asset_id: str
    original_filename: str
    asset_name: str

    thumbnail_path: str | None = None
    preview_path: str | None = None

    total_usage: int


class TopAssetsResponse(BaseModel):
    top_assets: list[AssetUsageResponse]