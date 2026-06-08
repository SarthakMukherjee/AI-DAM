from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.core.security.auth import decode_access_token
from app.models.user.user_model import User

bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    token = credentials.credentials

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

# All the role-based dependencies below stay exactly the same
def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin access required")
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["super_admin", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

def require_reviewer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["super_admin", "reviewer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reviewer access required")
    return current_user

def require_admin_or_reviewer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["super_admin", "admin", "reviewer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Reviewer access required")
    return current_user