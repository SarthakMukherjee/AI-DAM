import pytesseract

from PIL import Image


class OCRService:

    # -----------------------------------
    # EXTRACT TEXT FROM FILE PATH
    # existing method, unchanged
    # -----------------------------------

    @staticmethod
    def extract_text(
        image_path: str
    ) -> str:

        try:

            image = Image.open(image_path)

            extracted_text = (
                pytesseract.image_to_string(image)
            )

            return extracted_text.strip()

        except Exception as e:

            print(
                f"OCR extraction failed: {e}"
            )

            return ""

    # -----------------------------------
    # EXTRACT TEXT FROM PIL IMAGE
    # used by pdf_tagging_service for
    # scanned page OCR fallback
    # -----------------------------------

    @staticmethod
    def extract_text_from_image(
        image: Image.Image
    ) -> str:

        try:

            extracted_text = (
                pytesseract.image_to_string(image)
            )

            return extracted_text.strip()

        except Exception as e:

            print(
                f"OCR extraction from image failed: {e}"
            )

            return ""