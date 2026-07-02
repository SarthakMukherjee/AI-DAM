# This service:
# - collects extracted infos
# - builds AI context
# - asks LLM for meaningful tags
# - generates normalized searchable tags


import json
import os

from groq import Groq

from app.ai.ocr.ocr_service import OCRService
from app.ai.tagging.image_tagging_service import ImageTaggingService
from app.ai.tagging.video_tagging_service import VideoTaggingService
from app.ai.tagging.pdf_tagging_service import PDFTaggingService
from app.ai.tagging.tag_cleaner_service import TagCleanerService

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class AutoTaggingService:

    def __init__(self):

        self.image_service = ImageTaggingService()

        self.video_service = VideoTaggingService()

        self.pdf_service = PDFTaggingService()

        self.client = Groq(api_key=GROQ_API_KEY)

    # -----------------------------------
    # AI SUMMARY GENERATION
    # Produces a clean 1-2 sentence summary
    # from any structured context dict
    # -----------------------------------

    def generate_ai_summary(self, structured_context: dict) -> str:
        """
        Generate a concise 1-2 sentence plain-text summary of the asset
        using the Groq LLM.

        Args:
            structured_context: Dict with extracted data (caption, objects,
                                text, etc.) — same format used for tagging.

        Returns:
            A clean 1-2 sentence summary string, or empty string on failure.
        """
        prompt = f"""
        You are an AI digital asset management assistant.
        Based on the following extracted data from an asset, write a concise,
        factual 1-2 sentence summary suitable for a DAM system description.

        Rules:
        - Return ONLY the summary text, no JSON, no markdown.
        - Maximum 2 sentences.
        - Be specific about content, NOT generic.

        Extracted Data:
        {json.dumps(structured_context, indent=2)}
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AI SUMMARY] Failed: {e}")
            return ""

    # Written on a 30-06-26
    def suggest_metadata(
        self,
        asset_type: str,
        file_path: str,
        filename: str
    ) -> dict:

        asset_type = asset_type.lower()
        extracted_context = {}
        detected_type = "document"

        # 1. Extract context depending on file type
        if asset_type in ["jpg", "jpeg", "png", "webp", "gif"]:
            detected_type = "image"
            caption = self.image_service.generate_caption(file_path)
            detected_objects = self.image_service.detect_objects(file_path)
            try:
                extracted_text = OCRService.extract_text(file_path)
            except Exception:
                extracted_text = ""
            extracted_context = {
                "caption": caption,
                "objects": detected_objects,
                "ocr_text": extracted_text
            }
        elif asset_type == "pdf":
            detected_type = "pdf"
            extracted_text = self.pdf_service.extract_text(file_path)
            doc_metadata = self.pdf_service.extract_metadata(file_path)
            page_count = self.pdf_service.get_page_count(file_path)
            extracted_context = {
                "extracted_text": extracted_text[:3000],
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "keywords": doc_metadata.get("keywords", ""),
                "page_count": page_count
            }
        elif asset_type in ["mp4", "mov", "avi", "mkv", "webm"]:
            detected_type = "video"
            captions = self.video_service.generate_captions(file_path)
            detected_objects = self.video_service.detect_objects(file_path)
            combined_caption = ". ".join(captions) if captions else ""
            extracted_context = {
                "captions": captions,
                "objects": detected_objects,
                "combined_caption": combined_caption
            }
        else:
            extracted_context = {
                "filename": filename
            }

        prompt = f"""
        You are an AI DAM METADATA ASSISTANT.
        Your task is to analyze the extracted data of an asset and recommend values for its mandatory metadata fields.
        
        The mandatory metadata fields are:
        1. asset_name: A user-friendly, descriptive title for the asset (e.g. "Marketing Campaign Banner" instead of "marketing_banner_v2.png"). Generate this based on the filename and the extracted visual/text content.
        2. asset_type: Must be one of: "image", "video", "pdf", "document". Choose the most appropriate one.
        3. description: A clear, concise description summarizing the content of the asset (2-3 sentences max).
        4. created_by: Recommend a creator (e.g. from PDF metadata author field if present, or suggest a realistic placeholder/default value like "Admin" or "AI Ingest Service").
        5. owner: Recommend an owner (e.g. from PDF metadata, or suggest a realistic placeholder/default value like "Admin" or "Marketing Team").
        6. usage_rights: Recommend usage rights. Must be one of: "Internal Only", "Licensed", "Public Domain", "Restricted", "Royalty Free", "Creative Commons".

        You should STRICTLY follow the following rules:
        - Return ONLY valid JSON
        - No markdown
        - No explanations
        - Use the exact field keys: "asset_name", "asset_type", "description", "created_by", "owner", "usage_rights"

        Required JSON format:
        {{
            "asset_name": "...",
            "asset_type": "...",
            "description": "...",
            "created_by": "...",
            "owner": "...",
            "usage_rights": "..."
        }}

        Filename: {filename}
        Asset Type: {detected_type}
        Extracted Data:
        {json.dumps(extracted_context, indent=2)}
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        llm_response = response.choices[0].message.content
        parsed_response = json.loads(llm_response)
        return parsed_response
        
        # END

    # -----------------------------------
    # SHARED: LLM TAG GENERATION
    # takes structured context dict,
    # returns cleaned tags list
    # -----------------------------------

    def _generate_tags_from_context(
        self,
        structured_context: dict
    ) -> list[str]:

        prompt = f"""
        You are an AI DAM TAGGING ASSISTANT.

        Your task is to generate highly relevant enterprise DAM tags which should be semantic from the following extracted asset data.

        You should STRICTLY follow the following rules:
            - Return ONLY valid JSON
            - No markdown
            - No explanations
            - The "tags" field MUST be a flat array of strings
            - No duplicate tags
            - Generate concise semantic tags
            - Focus on DAM search relevance
            - Focus on marketing/business meaning

            Required JSON format (This JSON format is purely an example showcasing how I want your response to be):

            {{
                "tags":[
                        "enterprise",
                        "dashboard",
                        "analytics"
                        ]
            }}

            Extracted Data:
            {json.dumps(structured_context, indent=2)}
            """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        llm_response = response.choices[0].message.content

        parsed_response = json.loads(llm_response)

        print(parsed_response)

        generated_tags = parsed_response.get("tags", [])

        cleaned_tags = TagCleanerService.clean_tags(
            generated_tags
        )

        return cleaned_tags

    # -----------------------------------
    # IMAGE PIPELINE
    # -----------------------------------

    def process_image(
        self,
        image_path: str
    ) -> dict:

        caption = self.image_service.generate_caption(
            image_path
        )

        detected_objects = self.image_service.detect_objects(
            image_path
        )

        try:
            extracted_text = OCRService.extract_text(
                image_path
            )
        except Exception:
            extracted_text = ""

        structured_context = {
            "caption": caption,
            "objects": detected_objects,
            "ocr_text": extracted_text
        }

        cleaned_tags = self._generate_tags_from_context(
            structured_context
        )

        ai_summary = self.generate_ai_summary(structured_context)

        return {
            "ai_tags": cleaned_tags,
            "image_caption": caption,
            "detected_objects": detected_objects,
            "extracted_text": extracted_text,
            "searchable_tags": cleaned_tags,
            "enrichment_status": "completed",
            "ai_summary": ai_summary,
        }

    # -----------------------------------
    # VIDEO PIPELINE
    # -----------------------------------

    def process_video(
        self,
        video_path: str
    ) -> dict:

        captions = self.video_service.generate_captions(
            video_path
        )

        detected_objects = self.video_service.detect_objects(
            video_path
        )

        combined_caption = (
            ". ".join(captions)
            if captions
            else ""
        )

        structured_context = {
            "captions": captions,
            "objects": detected_objects,
            "combined_caption": combined_caption
        }

        cleaned_tags = self._generate_tags_from_context(
            structured_context
        )

        ai_summary = self.generate_ai_summary(structured_context)

        return {
            "ai_tags": cleaned_tags,
            "image_caption": combined_caption,
            "detected_objects": detected_objects,
            "extracted_text": "",
            "searchable_tags": cleaned_tags,
            "enrichment_status": "completed",
            "ai_summary": ai_summary,
        }

    # -----------------------------------
    # PDF PIPELINE
    # extracts text + doc metadata,
    # sends to LLM for semantic tags
    # -----------------------------------

    def process_pdf(
        self,
        pdf_path: str
    ) -> dict:

        extracted_text = self.pdf_service.extract_text(
            pdf_path
        )

        doc_metadata = self.pdf_service.extract_metadata(
            pdf_path
        )

        page_count = self.pdf_service.get_page_count(
            pdf_path
        )

        # truncate text to avoid LLM token limits
        # 3000 chars covers most doc summaries

        structured_context = {
            "extracted_text": extracted_text[:3000],
            "title": doc_metadata.get("title", ""),
            "author": doc_metadata.get("author", ""),
            "subject": doc_metadata.get("subject", ""),
            "keywords": doc_metadata.get("keywords", ""),
            "page_count": page_count
        }

        cleaned_tags = self._generate_tags_from_context(
            structured_context
        )

        ai_summary = self.generate_ai_summary(structured_context)

        return {
            "ai_tags": cleaned_tags,
            "image_caption": "",
            "detected_objects": [],
            "extracted_text": extracted_text,
            "searchable_tags": cleaned_tags,
            "enrichment_status": "completed",
            "ai_summary": ai_summary,
        }