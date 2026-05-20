from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import get_current_user
from app.core.security.hashing import hash_password, verify_password
from app.core.security.auth import create_access_token
from app.models.user.user_model import User

from app.schemas.user.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# -----------------------------------
# REGISTER
# open endpoint — anyone can register
# default role is "user"
# -----------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
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
# returns JWT access token
# -----------------------------------

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
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

    return {
        "access_token": token,
        "token_type": "bearer"
    }


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