import hashlib
import magic

from fastapi import HTTPException

ALLOWED_MIME_TYPES = [ 
    "image/jpeg",
    "image/png",
    "application/pdf",
    "video/mp4"
]

def calculate_file_hash(file_bytes: str) -> str:
    sha256 = hashlib.sha256()
    sha256.update(file_bytes)

    return sha256.hexdigest()

def detect_mime_type(file_path:str):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)

def validate_mime_type(mime_type: str):
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=404, 
            detail=f"Unsupported MIME type: {mime_type}"
        )