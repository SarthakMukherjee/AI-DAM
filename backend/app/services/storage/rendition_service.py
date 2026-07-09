import os
from PIL import Image
from sqlalchemy.orm import Session
from app.models.asset.asset_model import Asset
from app.models.asset.asset_rendition_model import AssetRendition
from app.services.storage.cloud_service import CloudService
from app.core.config.settings import settings

class RenditionService:
    @staticmethod
    def generate_image_renditions(asset: Asset, db: Session, local_path: str):
        # We assume local_path is an image file downloaded temporarily or available locally
        renditions = []
        
        # Define standard renditions
        specs = [
            {"name": "web-compressed", "width": 800, "height": None},
            {"name": "social-square", "width": 1080, "height": 1080}
        ]
        
        try:
            with Image.open(local_path) as img:
                for spec in specs:
                    img_copy = img.copy()
                    
                    if spec["width"] and spec["height"]:
                        # Crop to square / resize
                        img_copy.thumbnail((spec["width"], spec["height"]))
                    elif spec["width"]:
                        # Proportional resize
                        wpercent = (spec["width"] / float(img_copy.size[0]))
                        hsize = int((float(img_copy.size[1]) * float(wpercent)))
                        img_copy = img_copy.resize((spec["width"], hsize), Image.Resampling.LANCZOS)
                        
                    rendition_filename = f"{asset.id}_{spec['name']}.jpg"
                    rendition_path = os.path.join(settings.STORAGE_PATH, "temp", rendition_filename)
                    
                    # Ensure temp exists
                    os.makedirs(os.path.dirname(rendition_path), exist_ok=True)
                    
                    img_copy = img_copy.convert("RGB")
                    img_copy.save(rendition_path, format="JPEG", quality=85)
                    
                    # Upload to cloud
                    cloud_url = CloudService.upload(
                        file_path=rendition_path,
                        public_id=f"renditions/{rendition_filename}",
                        resource_type="image",
                        folder="ai-dam"
                    )
                    
                    if cloud_url:
                        rendition = AssetRendition(
                            asset_id=asset.id,
                            rendition_name=spec["name"],
                            storage_path=cloud_url,
                            mime_type="image/jpeg",
                            file_size=os.path.getsize(rendition_path),
                            width=img_copy.width,
                            height=img_copy.height
                        )
                        renditions.append(rendition)
                        
                    # Cleanup temp
                    if os.path.exists(rendition_path):
                        os.remove(rendition_path)
            
            return renditions
        except Exception as e:
            print(f"Error generating renditions: {e}")
            return []
