import uuid
import os
import aiofiles
import shutil

from fastapi import UploadFile
from app.core.config.settings import settings

# class StorageService:

#     async def save_original_file(self, upload_file:UploadFile):
#         extension = upload_file.filename.split(".")[-1]

#         unique_filename = f"{uuid.uuid4()}.{extension}"

#         save_path = os.path.join(
#             settings.STORAGE_PATH,
#             "originals",
#             unique_filename
#         )

#         async with aiofiles.open(save_path, "wb") as out_file:
#             content = await upload_file.read()
#             await out_file.write(content)

#             normalized_path = save_path.replace("\\", "/") #added on 15-05-26

#         return unique_filename, normalized_path, content

class StorageService:
    async def save_to_temp(self, file:UploadFile):

        extension = file.filename.split(".")[-1]

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
    
    def move_to_original(self, temp_path:str, filename:str):
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
