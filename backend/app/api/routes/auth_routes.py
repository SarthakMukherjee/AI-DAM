from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth_dependency import get_current_user
from app.core.security.hashing import hash_password, verify_password
from app.core.security.auth import create_access_token, decode_access_token
from app.core.security.token_blacklist import blacklist_token, cleanup_expired
from app.models.user.user_model import User

from app.schemas.user.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse
)

bearer_scheme = HTTPBearer(auto_error=False)


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
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(data={"sub": user.id, "role": user.role})

    # No more cookie - return token in body
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Login successful",
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        "id": user.id
    }

# -----------------------------------
# LOGOUT
# invalidates the JWT server-side
# via an in-memory token blacklist
# -----------------------------------

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials if credentials else None

    if token:
        # Decode to get the expiry time so the blacklist entry
        # can be auto-cleaned after the token would have expired anyway
        payload = decode_access_token(token)
        if payload and "exp" in payload:
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        else:
            # If we can't decode, still blacklist but assume max TTL
            from app.core.security.auth import ACCESS_TOKEN_EXPIRE_MINUTES
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )

        blacklist_token(token, expires_at)

    # Periodic cleanup — remove tokens that have naturally expired
    cleanup_expired()

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