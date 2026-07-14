# THIS SCRIPT HANDLES ORCHESTRATION ONLY

from app.ai.tagging.auto_tagging_service import AutoTaggingService


class EnrichmentPipeline:

    def __init__(self):

        self.auto_tagging_service = (
            AutoTaggingService()
        )

    def process_asset(
        self,
        asset_type: str,
        file_path: str
    ) -> dict:

        asset_type = asset_type.lower()

        # -----------------------------------
        # IMAGE PIPELINE
        # -----------------------------------

        if asset_type in ["jpg", "jpeg", "png", "webp", "gif"]:

            return (
                self.auto_tagging_service
                .process_image(file_path)
            )

        # -----------------------------------
        # PDF PIPELINE
        # -----------------------------------

        elif asset_type == "pdf":

            return (
                self.auto_tagging_service
                .process_pdf(file_path)
            )

        # -----------------------------------
        # VIDEO PIPELINE
        # -----------------------------------

        elif asset_type in ["mp4", "mov", "avi", "mkv", "webm"]:

            return (
                self.auto_tagging_service
                .process_video(file_path)
            )

        # -----------------------------------
        # WORD PIPELINE
        # -----------------------------------

        elif asset_type in ["doc", "docx"]:

            return (
                self.auto_tagging_service
                .process_word(file_path)
            )

        # -----------------------------------
        # EXCEL PIPELINE
        # -----------------------------------

        elif asset_type in ["xls", "xlsx"]:

            return (
                self.auto_tagging_service
                .process_excel(file_path)
            )

        # -----------------------------------
        # PPT PIPELINE
        # -----------------------------------

        elif asset_type in ["ppt", "pptx"]:

            return (
                self.auto_tagging_service
                .process_ppt(file_path)
            )

        # -----------------------------------
        # UNSUPPORTED
        # -----------------------------------

        return {
            "ai_tags": [],
            "image_caption": "",
            "detected_objects": [],
            "extracted_text": "",
            "searchable_tags": [],
            "enrichment_status": "unsupported_type"
        }