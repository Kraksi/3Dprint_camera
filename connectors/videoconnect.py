import cv2


class VideoStream:
    def __init__(self, src=0):
        self.src = src
        self.stream = cv2.VideoCapture(src)  # Инициализация видеопотока
        if not self.stream.isOpened():
            raise ValueError("Не удалось открыть видеопоток.")

    def get_frame(self):
        if not hasattr(self, 'stream') or not self.stream.isOpened():
            raise ValueError("Видеопоток не открыт.")

        ret, frame = self.stream.read()
        if not ret:
            raise ValueError("Не удалось получить кадр.")

        return frame

    def release(self):
        if hasattr(self, 'stream') and self.stream.isOpened():
            self.stream.release()


