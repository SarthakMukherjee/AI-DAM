# THIS SCRIPT HANDLES ORCHESTRATION ONLY

from app.ai.tagging.auto_tagging_service import AutoTaggingService

class EnrichmentPipeline:
    def __init__(self):
        self.auto_tagging_service = (
            AutoTaggingService()
        )

    def process_asset(self, asset_type:str, file_path:str):
        
        # IMAGE PIPELINE

        if asset_type.lower() in [
            "jpg",
            "jpeg",
            "png"
        ]:
            return (
                self.auto_tagging_service.process_image(file_path)
            )
        
        # PDF PIPELINE

        elif asset_type.lower() == "pdf":
            return {
                "message": (
                    "PDF pipeline not implemented yet"
                )
            }
        
        # VIDEO PIPELINE
        elif asset_type.lower() == "mp4":
            return {
                "message": (
                    "Video pipeline not implemented yet"
                )
            }
        
        return {"messsage": "Unsupported asset type"}
