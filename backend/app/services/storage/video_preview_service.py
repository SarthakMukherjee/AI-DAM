# VIDEO PREVIEW SERVICE

import os
import cv2

from app.core.config.settings import settings


class VideoPreviewService:

    def generate_preview(
        self,
        video_path: str,
        filename: str
    ):

        preview_dir = os.path.join(
            settings.STORAGE_PATH,
            "previews"
        )

        os.makedirs(preview_dir, exist_ok=True)

        preview_path = os.path.join(
            preview_dir,
            f"{filename}.jpg"
        )

        # -----------------------------------
        # OPEN VIDEO AND SEEK TO 1 SECOND
        # -----------------------------------

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video: {video_path}"
            )

        fps = cap.get(cv2.CAP_PROP_FPS) or 25

        # seek to 1 second in (same as ss=1 in ffmpeg)
        cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            int(fps * 1)
        )

        ret, frame = cap.read()

        cap.release()

        if not ret:
            # fallback to first frame
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()

        if not ret:
            raise RuntimeError(
                f"Could not extract frame from: {video_path}"
            )

        # -----------------------------------
        # WRITE PREVIEW JPEG
        # -----------------------------------

        cv2.imwrite(preview_path, frame)

        return preview_path.replace("\\", "/")