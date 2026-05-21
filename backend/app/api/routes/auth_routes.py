from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import get_current_user
from app.core.security.hashing import hash_password, verify_password
from app.core.security.auth import create_access_token
from app.models.user.user_model import User

from app.schemas.user.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse
)


limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# -----------------------------------
# REGISTER
# 3 requests per minute per IP
# -----------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("3/minute")
def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(User)
        .filter(User.email == body.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role="user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# -----------------------------------
# LOGIN
# 5 requests per minute per IP
# sets httpOnly cookie with JWT
# -----------------------------------

@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == body.email)
        .first()
    )

    if not user or not verify_password(
        body.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    token = create_access_token(
        data={"sub": user.id, "role": user.role}
    )

    # -----------------------------------
    # SET httpOnly COOKIE
    # httponly=True  → JS cannot read it
    # samesite="lax" → CSRF protection
    # secure=False   → set True in prod
    #                  (requires HTTPS)
    # max_age=3600   → 1 hour (matches JWT)
    # -----------------------------------

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,       # change to True in production
        max_age=3600
    )

    return {
        "message": "Login successful",
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        "id": user.id
    }


# -----------------------------------
# LOGOUT
# clears the httpOnly cookie
# -----------------------------------

@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )

    return {"message": "Logged out successfully"}


# -----------------------------------
# ME
# returns current authenticated user
# -----------------------------------

@router.get(
    "/me",
    response_model=UserResponse
)
def me(
    current_user: User = Depends(get_current_user)
):
    return current_user