import cv2

"""
Класс для получение видеопотока с использованием паттера singleton.
                   
Для проекта нет необходимости создавать несколько экземпляров класса, поэтому лучше использовать паттер, чтобы 
ограничить создание экзепляров.

"""


class VideoStreamSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VideoStreamSingleton, cls).__new__(cls)
            cls._instance.cap = cv2.VideoCapture(*args, **kwargs)
            if not cls._instance.cap.isOpened():
                raise ValueError("Не удалось открыть видеопоток.")
        return cls._instance

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError("Не удалось получить кадр.")
        return frame

    def release(self):
        if self.cap.isOpened():
            self.cap.release()


