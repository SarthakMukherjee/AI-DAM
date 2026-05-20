# PDF PREVIEW SERVICE

import os
import fitz

from app.core.config.settings import settings

class PDFPreviewService:
    
    def generate_preview(self, pdf_path, filename:str):
        
        document = fitz.open(pdf_path)

        page = document.load_page(0)

        pix = page.get_pixmap()

        preview_path = os.path.join(
            settings.STORAGE_PATH,
            "previews",
            f"{filename}.png"
        )

        pix.save(preview_path)

        return preview_path.replace("\\","/")