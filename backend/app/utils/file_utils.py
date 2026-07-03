import hashlib
import mimetypes

import filetype

from fastapi import HTTPException


ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "application/pdf",
    "video/mp4"
]


# -----------------------------------
# FILE HASH
# -----------------------------------

def calculate_file_hash(
    file_bytes: bytes
) -> str:

    sha256 = hashlib.sha256()
    sha256.update(file_bytes)
    return sha256.hexdigest()


# -----------------------------------
# MIME TYPE DETECTION
# filetype reads magic bytes (no DLL)
# falls back to mimetypes from extension
# -----------------------------------

def detect_mime_type(
    file_path: str
) -> str:

    kind = filetype.guess(file_path)

    if kind is not None:
        return kind.mime

    mime, _ = mimetypes.guess_type(file_path)

    return mime or "application/octet-stream"


# -----------------------------------
# MIME TYPE FROM FILENAME ONLY
# used when only a filename is available
# -----------------------------------

def get_mime_type(
    filename: str
) -> str:

    mime, _ = mimetypes.guess_type(filename)

    return mime or "application/octet-stream"


# -----------------------------------
# MIME TYPE VALIDATION
# -----------------------------------

def validate_mime_type(
    mime_type: str
) -> None:
    # All file types (images, videos, documents, archives, etc.) are now permitted.
    pass