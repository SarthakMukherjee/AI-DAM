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
from app.ai.tagging.tag_cleaner_service import TagCleanerService

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class AutoTaggingService:

    def __init__(self):

        self.image_service = ImageTaggingService()

        self.video_service = VideoTaggingService()

        self.client = Groq(api_key=GROQ_API_KEY)

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

        # EXTRACTION LAYER

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

        # BUILD CONTEXT

        structured_context = {
            "caption": caption,
            "objects": detected_objects,
            "ocr_text": extracted_text
        }

        # LLM INTELLIGENCE

        cleaned_tags = self._generate_tags_from_context(
            structured_context
        )

        return {
            "ai_tags": cleaned_tags,
            "image_caption": caption,
            "detected_objects": detected_objects,
            "extracted_text": extracted_text,
            "searchable_tags": cleaned_tags,
            "enrichment_status": "completed"
        }

    # -----------------------------------
    # VIDEO PIPELINE
    # samples frames, captions each,
    # detects objects across all frames,
    # sends aggregated context to LLM
    # -----------------------------------

    def process_video(
        self,
        video_path: str
    ) -> dict:

        # EXTRACTION LAYER

        captions = self.video_service.generate_captions(
            video_path
        )

        detected_objects = self.video_service.detect_objects(
            video_path
        )

        # AGGREGATE CAPTIONS
        # join all frame captions into one
        # context string for the LLM

        combined_caption = (
            ". ".join(captions)
            if captions
            else ""
        )

        # BUILD CONTEXT

        structured_context = {
            "captions": captions,
            "objects": detected_objects,
            "combined_caption": combined_caption
        }

        # LLM INTELLIGENCE

        cleaned_tags = self._generate_tags_from_context(
            structured_context
        )

        return {
            "ai_tags": cleaned_tags,
            "image_caption": combined_caption,
            "detected_objects": detected_objects,
            "extracted_text": "",
            "searchable_tags": cleaned_tags,
            "enrichment_status": "completed"
        }