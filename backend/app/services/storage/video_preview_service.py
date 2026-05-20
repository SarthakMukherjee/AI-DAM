# VIDEO PREVIEW SERVICE

import os
import ffmpeg

from app.core.config.settings import settings


class VideoPreviewService:

    def generate_preview(
        self,
        video_path: str,
        filename: str
    ):

        preview_path = os.path.join(
            settings.STORAGE_PATH,
            "previews",
            f"{filename}.jpg"
        )

        (
            ffmpeg
            .input(video_path, ss=1)
            .output(preview_path, vframes=1)
            .run(overwrite_output=True)
        )

        return preview_path.replace("\\","/")