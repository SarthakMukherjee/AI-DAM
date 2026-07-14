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
from app.ai.tagging.word_tagging_service import WordTaggingService
from app.ai.tagging.excel_tagging_service import ExcelTaggingService
from app.ai.tagging.ppt_tagging_service import PPTTaggingService
from app.ai.tagging.tag_cleaner_service import TagCleanerService

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class AutoTaggingService:

    def __init__(self):

        self.image_service = ImageTaggingService()

        self.video_service = VideoTaggingService()

        self.pdf_service = PDFTaggingService()
        
        self.word_service = WordTaggingService()
        self.excel_service = ExcelTaggingService()
        self.ppt_service = PPTTaggingService()

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
        elif asset_type in ["doc", "docx"]:
            detected_type = "document"
            extracted_text = self.word_service.extract_text(file_path)
            doc_metadata = self.word_service.extract_metadata(file_path)
            extracted_context = {
                "extracted_text": extracted_text[:3000],
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "keywords": doc_metadata.get("keywords", "")
            }
        elif asset_type in ["xls", "xlsx"]:
            detected_type = "document"
            extracted_text = self.excel_service.extract_text(file_path)
            doc_metadata = self.excel_service.extract_metadata(file_path)
            extracted_context = {
                "extracted_text": extracted_text[:3000],
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "keywords": doc_metadata.get("keywords", "")
            }
        elif asset_type in ["ppt", "pptx"]:
            detected_type = "pitch_deck"
            extracted_text = self.ppt_service.extract_text(file_path)
            doc_metadata = self.ppt_service.extract_metadata(file_path)
            extracted_context = {
                "extracted_text": extracted_text[:3000],
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "keywords": doc_metadata.get("keywords", "")
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
        You are an AI DAM METADATA ASSISTANT for an Enterprise Digital Asset Management system.
        Your task is to analyze the extracted data of an asset and recommend values for its metadata fields.
        
        The metadata fields you MUST recommend are:

        MANDATORY FIELDS:
        1. asset_name: A user-friendly, descriptive title (e.g. "Marketing Campaign Banner" not "banner_v2.png").
        2. asset_type: Must be one of: "image", "video", "pdf", "document", "banner", "brochure", "social_creative", "logo", "pitch_deck", "campaign_file".
        3. description: A clear, concise description of the asset content (2-3 sentences max).
        4. created_by: Infer from metadata (e.g. PDF author) or use "Admin".
        5. owner: Infer from metadata or use "Marketing Team".
        6. usage_rights: Must be one of: "Internal Only", "Licensed", "Public Domain", "Restricted", "Royalty Free", "Creative Commons".

        BUSINESS CONTEXT FIELDS (infer from content, visuals, and subject matter):
        7. domain: The business domain this asset belongs to. Must be one of: "AI", "Staffing", "Marketing", "Sales", "Finance", "HR", "Operations", "Healthcare", "Tech", "Design".
        8. use_case: Must be one of: "email", "presentation", "website", "campaign", "sales", "social_media", "advertisment".
        9. audience: Must be one of: "b2b", "enterprise", "startup", "consumer", "partner".
        10. funnel_stage: Must be one of: "awareness", "consideration", "conversion".

        CONTENT FIELDS:
        11. tone: Must be one of: "professional", "casual", "formal", "friendly", "technical", "creative".
        12. keywords: A comma-separated string of 3-6 relevant keywords derived from the content.

        RULES:
        - Return ONLY valid JSON with EXACTLY these 12 keys
        - No markdown, no explanations, no code blocks
        - Every field is required — never return null or empty string
        - Infer intelligently from the content; if uncertain, pick the most likely value

        Required JSON format:
        {{
            "asset_name": "...",
            "asset_type": "...",
            "description": "...",
            "created_by": "...",
            "owner": "...",
            "usage_rights": "...",
            "domain": "...",
            "use_case": "...",
            "audience": "...",
            "funnel_stage": "...",
            "tone": "...",
            "keywords": "..."
        }}

        Filename: {filename}
        Detected File Type: {detected_type}
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

    # -----------------------------------
    # WORD PIPELINE
    # -----------------------------------

    def process_word(
        self,
        word_path: str
    ) -> dict:

        extracted_text = self.word_service.extract_text(word_path)
        doc_metadata = self.word_service.extract_metadata(word_path)

        structured_context = {
            "extracted_text": extracted_text[:3000],
            "title": doc_metadata.get("title", ""),
            "author": doc_metadata.get("author", ""),
            "subject": doc_metadata.get("subject", ""),
            "keywords": doc_metadata.get("keywords", "")
        }

        cleaned_tags = self._generate_tags_from_context(structured_context)
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

    # -----------------------------------
    # EXCEL PIPELINE
    # -----------------------------------

    def process_excel(
        self,
        excel_path: str
    ) -> dict:

        extracted_text = self.excel_service.extract_text(excel_path)
        doc_metadata = self.excel_service.extract_metadata(excel_path)

        structured_context = {
            "extracted_text": extracted_text[:3000],
            "title": doc_metadata.get("title", ""),
            "author": doc_metadata.get("author", ""),
            "subject": doc_metadata.get("subject", ""),
            "keywords": doc_metadata.get("keywords", "")
        }

        cleaned_tags = self._generate_tags_from_context(structured_context)
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

    # -----------------------------------
    # PPT PIPELINE
    # -----------------------------------

    def process_ppt(
        self,
        ppt_path: str
    ) -> dict:

        extracted_text = self.ppt_service.extract_text(ppt_path)
        doc_metadata = self.ppt_service.extract_metadata(ppt_path)

        structured_context = {
            "extracted_text": extracted_text[:3000],
            "title": doc_metadata.get("title", ""),
            "author": doc_metadata.get("author", ""),
            "subject": doc_metadata.get("subject", ""),
            "keywords": doc_metadata.get("keywords", "")
        }

        cleaned_tags = self._generate_tags_from_context(structured_context)
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