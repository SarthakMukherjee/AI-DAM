# THUMB NAIL GENERATION SERVICE

import os

from PIL import Image
from app.core.config.settings import settings

class ThumbnailService:
    def generate_image_thumbnail(self, image_path, filename: str):
        thumbnail_name = filename

        thumbnail_path = os.path.join(
            settings.STORAGE_PATH,
            "thumbnails",
            thumbnail_name
        )

        image = Image.open(image_path)
        image.thumbnail((300,300))
        image.save(thumbnail_path)

        return thumbnail_path.replace("\\", "/")