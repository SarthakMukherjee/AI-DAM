import cv2

class ImageUtils:
    @staticmethod
    def load_image(image_path:str):
        return cv2.imread(image_path)