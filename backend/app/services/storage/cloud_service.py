import os
import cloudinary
import cloudinary.uploader

from app.core.config.settings import settings


# -----------------------------------
# CONFIGURE CLOUDINARY
# -----------------------------------

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class CloudService:

    # -----------------------------------
    # UPLOAD FILE TO CLOUDINARY
    # returns public URL on success
    # returns None on failure (fallback)
    # -----------------------------------

    @staticmethod
    def upload(
        file_path: str,
        public_id: str,
        resource_type: str = "auto",
        folder: str = "ai-dam"
    ) -> str | None:

        try:

            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                folder=folder,
                resource_type=resource_type,
                overwrite=True
            )

            return result.get("secure_url")

        except Exception as e:

            print(
                f"Cloudinary upload failed: {e}"
            )

            return None

    # -----------------------------------
    # UPLOAD BYTES TO CLOUDINARY
    # for in-memory files (thumbnails etc)
    # -----------------------------------

    @staticmethod
    def upload_bytes(
        file_bytes: bytes,
        public_id: str,
        resource_type: str = "auto",
        folder: str = "ai-dam"
    ) -> str | None:

        try:

            result = cloudinary.uploader.upload(
                file_bytes,
                public_id=public_id,
                folder=folder,
                resource_type=resource_type,
                overwrite=True
            )

            return result.get("secure_url")

        except Exception as e:

            print(
                f"Cloudinary bytes upload failed: {e}"
            )

            return None

    # -----------------------------------
    # DELETE FROM CLOUDINARY
    # -----------------------------------

    @staticmethod
    def delete(
        public_id: str,
        resource_type: str = "image"
    ) -> bool:

        try:

            cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )

            return True

        except Exception as e:

            print(
                f"Cloudinary delete failed: {e}"
            )

            return False