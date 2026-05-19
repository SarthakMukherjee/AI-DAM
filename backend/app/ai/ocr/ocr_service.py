import pytesseract
from PIL import Image

class OCRService:

    @staticmethod
    def extract_text(image_path) -> str:
        try:
            image = Image.open(image_path)

            extracted_text = pytesseract.image_to_string(image)

            return extracted_text.strip()
        
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
