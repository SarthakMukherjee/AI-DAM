import os
import shutil

from PIL import Image
import pytesseract


def configure_tesseract():
    """
    Configure Tesseract path dynamically.
    Priority:
    1. ENV variable
    2. System PATH
    3. Common install locations
    """

    # 1. ENV VARIABLE
    env_path = os.getenv("TESSERACT_CMD")

    if env_path and os.path.exists(env_path):

        pytesseract.pytesseract.tesseract_cmd = env_path
        return

    # 2. SYSTEM PATH
    system_path = shutil.which("tesseract")

    if system_path:

        pytesseract.pytesseract.tesseract_cmd = system_path
        return

    # 3. COMMON WINDOWS PATHS
    possible_paths = [

        r"C:\Program Files\Tesseract-OCR\tesseract.exe",

        r"C:\Users\monojitdas\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]

    for path in possible_paths:

        if os.path.exists(path):

            pytesseract.pytesseract.tesseract_cmd = path
            return

    raise RuntimeError(
        "Tesseract OCR not found. "
        "Install Tesseract or configure TESSERACT_CMD."
    )


# Configure once on startup
configure_tesseract()


class OCRService:

    # -----------------------------------
    # EXTRACT TEXT FROM FILE PATH
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