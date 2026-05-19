# # THIS SERVICE HANDLES IMAGE CAPTION GENERATION AND TAG EXTRACTION

# from PIL import Image
# from transformers import (
#     pipeline,
#     BlipProcessor,
#     BlipForConditionalGeneration
# )
# from ultralytics import YOLO


# class ImageTaggingService:
#     def __init__(self):

#         # self.caption_pipeline = pipeline(
#         #     "image-text-to-text",
#         #     model="Salesforce/blip-image-captioning-base"
#         # )
#         self.processor = (
#             BlipProcessor.from_pretrained(
#                 "Salesforce/blip-image-captioning-base"
#             )
#         )

#         self.caption_model = (
#             BlipForConditionalGeneration.from_pretrained(
#                 "Salesforce/blip-image-captioning-base"
#             )
#         )

#         self.object_detector = YOLO(
#             "yolov8n.pt"
#         )


#     # IMAGE CAPTION

#     def generate_caption(self, image_path:str) -> str:

#         result = self.caption_pipeline(image_path)

#         if result and len(result) > 0:
#             return result[0]["generated"]
        
#         return ""

#     # OBEJCT DETECTION

#     def detect_objects(self, image_path:str):
#         results = self.object_detector(image_path)

#         detected_objects = []

#         for result in results:
#             boxes = result.boxes

#             for box in boxes:

#                 class_id = int(box.cls[0])

#                 class_name = result.names[class_id]

#                 detected_objects.append(class_name)

#                 return list(set(detected_objects))

        
from PIL import Image

from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration
)

from ultralytics import YOLO


class ImageTaggingService:

    def __init__(self):

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
    # IMAGE CAPTIONING
    # -----------------------------------

    def generate_caption(
        self,
        image_path: str
    ) -> str:

        try:

            image = (
                Image.open(image_path)
                .convert("RGB")
            )

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
                f"Caption generation failed: {e}"
            )

            return ""

    # -----------------------------------
    # OBJECT DETECTION
    # -----------------------------------

    def detect_objects(
        self,
        image_path: str
    ):

        try:

            results = self.object_detector(
                image_path
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
                f"Object detection failed: {e}"
            )

            return []
    