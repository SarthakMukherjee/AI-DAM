# PDF PREVIEW SERVICE

import os
import fitz  # PyMuPDF

from app.core.config.settings import settings


class PDFPreviewService:

    def generate_preview(
        self,
        pdf_path: str,
        filename: str
    ):

        # -----------------------------------
        # CREATE PREVIEW DIRECTORY
        # one folder per PDF file
        # stores page-by-page images
        # -----------------------------------

        preview_dir = os.path.join(
            settings.STORAGE_PATH,
            "previews",
            filename
        )

        os.makedirs(preview_dir, exist_ok=True)

        document = fitz.open(pdf_path)

        page_paths = []

        for page_index in range(len(document)):

            page = document.load_page(page_index)

            # -----------------------------------
            # RENDER AT 2X RESOLUTION
            # matrix scale=2 gives crisp
            # images for browser rendering
            # -----------------------------------

            mat = fitz.Matrix(2, 2)

            pix = page.get_pixmap(matrix=mat)

            page_filename = (
                f"page_{page_index + 1}.png"
            )

            page_path = os.path.join(
                preview_dir,
                page_filename
            )

            pix.save(page_path)

            page_paths.append(
                page_path.replace("\\", "/")
            )

        document.close()

        # -----------------------------------
        # RETURN FIRST PAGE AS PREVIEW PATH
        # asset_service stores this in
        # preview_path column; the route
        # uses it for single-image preview
        # -----------------------------------

        return page_paths[0] if page_paths else None