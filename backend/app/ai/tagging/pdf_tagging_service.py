import fitz  # PyMuPDF

from PIL import Image
from io import BytesIO

from app.ai.ocr.ocr_service import OCRService


class PDFTaggingService:

    # -----------------------------------
    # TEXT EXTRACTION
    # tries direct text extraction first
    # falls back to OCR for scanned pages
    # -----------------------------------

    def extract_text(
        self,
        pdf_path: str
    ) -> str:

        try:

            document = fitz.open(pdf_path)

            all_text = []

            for page in document:

                # -----------------------------------
                # DIRECT TEXT EXTRACTION
                # works for text-based PDFs
                # -----------------------------------

                page_text = page.get_text().strip()

                if page_text:

                    all_text.append(page_text)

                else:

                    # -----------------------------------
                    # OCR FALLBACK
                    # for scanned/image-only pages
                    # -----------------------------------

                    ocr_text = self._ocr_page(page)

                    if ocr_text:
                        all_text.append(ocr_text)

            document.close()

            return "\n".join(all_text).strip()

        except Exception as e:

            print(
                f"PDF text extraction failed: {e}"
            )

            return ""

    # -----------------------------------
    # OCR A SINGLE PAGE
    # renders page to image then runs OCR
    # -----------------------------------

    def _ocr_page(
        self,
        page: fitz.Page
    ) -> str:

        try:

            pix = page.get_pixmap()

            img_bytes = pix.tobytes("png")

            image = Image.open(
                BytesIO(img_bytes)
            )

            extracted = (
                OCRService.extract_text_from_image(
                    image
                )
            )

            return extracted

        except Exception as e:

            print(
                f"OCR page fallback failed: {e}"
            )

            return ""

    # -----------------------------------
    # METADATA EXTRACTION
    # pulls title, author, subject
    # from PDF document properties
    # -----------------------------------

    def extract_metadata(
        self,
        pdf_path: str
    ) -> dict:

        try:

            document = fitz.open(pdf_path)

            meta = document.metadata

            document.close()

            return {
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "subject": meta.get("subject", ""),
                "keywords": meta.get("keywords", "")
            }

        except Exception as e:

            print(
                f"PDF metadata extraction failed: {e}"
            )

            return {
                "title": "",
                "author": "",
                "subject": "",
                "keywords": ""
            }

    # -----------------------------------
    # PAGE COUNT
    # -----------------------------------

    def get_page_count(
        self,
        pdf_path: str
    ) -> int:

        try:

            document = fitz.open(pdf_path)

            count = document.page_count

            document.close()

            return count

        except Exception as e:

            print(
                f"Page count failed: {e}"
            )

            return 0