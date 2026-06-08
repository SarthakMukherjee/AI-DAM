import uuid
import os
import shutil

from fastapi import UploadFile
from app.core.config.settings import settings


class StorageService:

    def __init__(self):
        # ensure required directories exist on startup
        for folder in ["temp", "originals", "thumbnails", "previews"]:
            os.makedirs(
                os.path.join(settings.STORAGE_PATH, folder),
                exist_ok=True
            )

    async def save_to_temp(self, file: UploadFile):
        extension = file.filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{extension}"

        temp_path = os.path.join(
            settings.STORAGE_PATH,
            "temp",
            unique_filename
        )

        content = await file.read()

        with open(temp_path, "wb") as buffer:
            buffer.write(content)

        return (
            unique_filename,
            temp_path.replace("\\", "/"),
            content
        )

    def move_to_original(self, temp_path: str, filename: str):
        original_path = os.path.join(
            settings.STORAGE_PATH,
            "originals",
            filename
        )

        shutil.move(temp_path, original_path)

        return original_path.replace("\\", "/")

    def delete_temp_file(self, temp_path: str):
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def delete_local_file(self, file_path: str):
        """Delete local file after successful cloud upload."""
        try:
            if file_path and os.path.exists(file_path) and not file_path.startswith("http"):
                os.remove(file_path)
        except Exception as e:
            print(f"[STORAGE] Failed to delete local file {file_path}: {e}")