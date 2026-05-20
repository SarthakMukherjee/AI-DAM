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
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateRoleRequest(BaseModel):
    role: str  # admin / reviewer / user


# -----------------------------------
# REVIEW SCHEMAS
# -----------------------------------

class ReviewRequest(BaseModel):
    reason: Optional[str] = None


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
    total_usage: int


class TopAssetsResponse(BaseModel):
    top_assets: list[AssetUsageResponse]