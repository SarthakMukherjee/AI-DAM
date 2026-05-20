import os
from app.core.config.settings import settings

DIRECTORIES = [
    "originals",
    "thumbnails",
    "previews",
    "archived",
    "temp"
]

def initialize_storage():
    for directory in DIRECTORIES:
        path = os.path.join(settings.STORAGE_PATH, directory)

        os.makedirs(path, exist_ok=True)