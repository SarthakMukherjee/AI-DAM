import os

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from dotenv import load_dotenv
load_dotenv()
from app.core.config.settings import settings


# -----------------------------------
# JWT CONFIG
# add these to your .env file:
# JWT_SECRET_KEY=your-secret-key
# JWT_ALGORITHM=HS256
# -----------------------------------

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM

# 1 hour expiry
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# -----------------------------------
# CREATE ACCESS TOKEN
# -----------------------------------

def create_access_token(
    data: dict
) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# -----------------------------------
# DECODE + VERIFY TOKEN
# returns payload dict or None
# -----------------------------------

def decode_access_token(
    token: str
) -> dict | None:

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        return payload

    except JWTError:

        return None