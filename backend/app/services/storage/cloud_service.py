import os
import shutil

from app.core.config.settings import settings

# Configure Cloudinary only if keys are present and backend is cloudinary
if getattr(settings, "STORAGE_BACKEND", "local").lower() == "cloudinary" and getattr(settings, "CLOUDINARY_CLOUD_NAME", None):
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )


class CloudService:

    # -----------------------------------
    # UPLOAD FILE TO STORAGE BACKEND
    # Supports: 'local' (filesystem), 's3' (AWS S3 future), 'cloudinary'
    # returns URL or file path on success
    # -----------------------------------

    @staticmethod
    def upload(
        file_path: str,
        public_id: str,
        resource_type: str = "auto",
        folder: str = "ai-dam"
    ) -> str | None:
        backend = getattr(settings, "STORAGE_BACKEND", "local").lower()

        # 1. LOCAL STORAGE BACKEND
        if backend == "local":
            return file_path.replace("\\", "/")

        # 2. AWS S3 STORAGE BACKEND (Future Migration Hook)
        elif backend == "s3":
            # Example S3 integration:
            # s3_bucket = getattr(settings, "AWS_S3_BUCKET", "ai-dam-bucket")
            # s3_key = f"{folder}/{public_id}.{file_path.split('.')[-1]}"
            # s3_client.upload_file(file_path, s3_bucket, s3_key)
            # return f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
            print("[STORAGE] S3 backend selected but S3 client not configured yet. Using local fallback.")
            return file_path.replace("\\", "/")

        # 3. CLOUDINARY BACKEND
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                folder=folder,
                resource_type=resource_type,
                overwrite=True
            )
            return result.get("secure_url")
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            return None

    # -----------------------------------
    # UPLOAD BYTES TO STORAGE BACKEND
    # -----------------------------------

    @staticmethod
    def upload_bytes(
        file_bytes: bytes,
        public_id: str,
        resource_type: str = "auto",
        folder: str = "ai-dam"
    ) -> str | None:
        backend = getattr(settings, "STORAGE_BACKEND", "local").lower()

        if backend == "local" or backend == "s3":
            out_path = os.path.join(settings.STORAGE_PATH, f"{public_id.replace('/', '_')}.bin")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(file_bytes)
            return out_path.replace("\\", "/")

        try:
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                file_bytes,
                public_id=public_id,
                folder=folder,
                resource_type=resource_type,
                overwrite=True
            )
            return result.get("secure_url")
        except Exception as e:
            print(f"Cloudinary bytes upload failed: {e}")
            return None

    # -----------------------------------
    # DELETE FROM STORAGE BACKEND
    # -----------------------------------

    @staticmethod
    def delete(
        public_id: str,
        resource_type: str = "image"
    ) -> bool:
        backend = getattr(settings, "STORAGE_BACKEND", "local").lower()

        if backend == "local" or backend == "s3":
            return True

        try:
            import cloudinary.uploader
            cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            return True
        except Exception as e:
            print(f"Cloudinary delete failed: {e}")
            return False