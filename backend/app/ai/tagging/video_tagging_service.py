import cv2
import os
import tempfile

from PIL import Image

from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration
)

from ultralytics import YOLO


class VideoTaggingService:

    def __init__(
        self,
        frame_interval: int = 5
    ):

        # -----------------------------------
        # FRAME SAMPLING INTERVAL (SECONDS)
        # -----------------------------------

        self.frame_interval = frame_interval

        # -----------------------------------
        # BLIP PROCESSOR
        # -----------------------------------

        self.processor = (
            BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
        )

        # -----------------------------------
        # BLIP MODEL
        # -----------------------------------

        self.caption_model = (
            BlipForConditionalGeneration
            .from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
        )

        # -----------------------------------
        # YOLO MODEL
        # -----------------------------------

        self.object_detector = YOLO(
            "yolov8n.pt"
        )

    # -----------------------------------
    # FRAME EXTRACTION
    # -----------------------------------

    def extract_frames(
        self,
        video_path: str
    ) -> list[Image.Image]:

        try:

            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                print(
                    f"Could not open video: {video_path}"
                )
                return []

            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps <= 0:
                fps = 25

            frame_step = int(fps * self.frame_interval)

            frames = []
            frame_index = 0

            while True:

                ret, frame = cap.read()

                if not ret:
                    break

                if frame_index % frame_step == 0:

                    rgb_frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    pil_image = Image.fromarray(
                        rgb_frame
                    )

                    frames.append(pil_image)

                frame_index += 1

            cap.release()

            return frames

        except Exception as e:

            print(
                f"Frame extraction failed: {e}"
            )

            return []

    # -----------------------------------
    # CAPTION FOR A SINGLE FRAME
    # -----------------------------------

    def _caption_frame(
        self,
        image: Image.Image
    ) -> str:

        try:

            inputs = self.processor(
                image,
                return_tensors="pt"
            )

            output = (
                self.caption_model.generate(
                    **inputs
                )
            )

            caption = self.processor.decode(
                output[0],
                skip_special_tokens=True
            )

            return caption

        except Exception as e:

            print(
                f"Frame caption failed: {e}"
            )

            return ""

    # -----------------------------------
    # OBJECT DETECTION FOR A SINGLE FRAME
    # -----------------------------------

    def _detect_frame_objects(
        self,
        image: Image.Image
    ) -> list[str]:

        try:

            with tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False
            ) as tmp:

                tmp_path = tmp.name
                image.save(tmp_path)

            results = self.object_detector(
                tmp_path
            )

            detected_objects = []

            for result in results:

                boxes = result.boxes

                for box in boxes:

                    class_id = int(
                        box.cls[0]
                    )

                    class_name = (
                        result.names[class_id]
                    )

                    detected_objects.append(
                        class_name
                    )

            return list(
                set(detected_objects)
            )

        except Exception as e:

            print(
                f"Frame object detection failed: {e}"
            )

            return []

        finally:

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -----------------------------------
    # VIDEO CAPTIONING
    # generates one caption per sampled
    # frame, returns all captions as list
    # -----------------------------------

    def generate_captions(
        self,
        video_path: str
    ) -> list[str]:

        frames = self.extract_frames(video_path)

        if not frames:
            return []

        captions = []

        for frame in frames:

            caption = self._caption_frame(frame)

            if caption:
                captions.append(caption)

        return captions

    # -----------------------------------
    # VIDEO OBJECT DETECTION
    # aggregates and deduplicates detected
    # objects across all sampled frames
    # -----------------------------------

    def detect_objects(
        self,
        video_path: str
    ) -> list[str]:

        frames = self.extract_frames(video_path)

        if not frames:
            return []

        all_objects = []

        for frame in frames:

            objects = self._detect_frame_objects(
                frame
            )

            all_objects.extend(objects)

        return list(set(all_objects))