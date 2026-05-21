from fastapi import Depends, HTTPException, Request, status

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.core.security.auth import decode_access_token
from app.models.user.user_model import User


# -----------------------------------
# GET CURRENT USER
# reads JWT from httpOnly cookie
# raises 401 if missing/invalid/expired
# -----------------------------------

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id: str = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    return user


# -----------------------------------
# REQUIRE SUPER ADMIN
# -----------------------------------

def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required"
        )

    return current_user


# -----------------------------------
# REQUIRE ADMIN
# super_admin + admin pass
# -----------------------------------

def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# -----------------------------------
# REQUIRE REVIEWER
# super_admin + reviewer pass
# -----------------------------------

def require_reviewer(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role not in ["super_admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer access required"
        )

    return current_user


# -----------------------------------
# REQUIRE ADMIN OR REVIEWER
# super_admin + admin + reviewer pass
# -----------------------------------

def require_admin_or_reviewer(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role not in [
        "super_admin",
        "admin",
        "reviewer"
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Reviewer access required"
        )

    return current_user