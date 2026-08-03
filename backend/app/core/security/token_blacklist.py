"""
token_blacklist.py
------------------
In-memory JWT token blacklist for server-side logout invalidation.

Blacklisted tokens are stored with their expiry time and automatically
purged on each cleanup pass to prevent unbounded memory growth.

NOTE: This is an in-memory store — it is cleared on server restart.
For a distributed / multi-process deployment, replace with a Redis-backed
store (e.g. redis.setex with TTL = token remaining lifetime).
"""

import threading
from datetime import datetime, timezone


# -----------------------------------
# THREAD-SAFE BLACKLIST STORE
# Maps token (str) → expiry (datetime)
# -----------------------------------

_blacklist: dict[str, datetime] = {}
_lock = threading.Lock()


def blacklist_token(token: str, expires_at: datetime) -> None:
    """
    Add a token to the blacklist.
    It will be kept until its natural expiry, then cleaned up.
    """
    with _lock:
        _blacklist[token] = expires_at


def is_blacklisted(token: str) -> bool:
    """Check if a token has been blacklisted (i.e. logged out)."""
    with _lock:
        return token in _blacklist


def cleanup_expired() -> int:
    """
    Remove expired tokens from the blacklist to free memory.
    Returns the number of tokens removed.
    """
    now = datetime.now(timezone.utc)
    with _lock:
        expired_keys = [
            t for t, exp in _blacklist.items() if exp <= now
        ]
        for key in expired_keys:
            del _blacklist[key]
        return len(expired_keys)
