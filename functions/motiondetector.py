import cv2
import time
from observer.observer import Subject


class MotionDetector(Subject):
    def __init__(self, min_area=1000, min_motion_duration=5.0, motion_cooldown=10.0):
        super().__init__()
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
        self.min_area = min_area  # Минимальная площадь контура для учета движения
        self.min_motion_duration = min_motion_duration  # Минимальная продолжительность движения
        self.motion_cooldown = motion_cooldown  # Время "охлаждения" перед завершением движения
        self.motion_start_time = None  # Время начала движения
        self.last_motion_time = None  # Время последнего обнаруженного движения
        self.motion_active = False  # Флаг, указывающий, активно ли движение

    def process_frame(self, frame):
        # Преобразуем кадр в оттенки серого
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Применяем метод вычитания фона
        fg_mask = self.bg_subtractor.apply(gray)

        # Применяем морфологические операции для удаления шума
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Находим контуры
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False

        # Проверка наличия движения
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                break  # Если найдено движение, прерываем цикл

        # Логика обработки времени движения
        current_time = time.time()

        if motion_detected:
            if not self.motion_active:
                # Движение началось
                self.motion_start_time = current_time
                self.last_motion_time = current_time
                self.motion_active = True
                print("Движение началось.")
            else:
                # Движение продолжается, обновляем время последнего движения
                self.last_motion_time = current_time
        else:
            if self.motion_active:
                # Движение не обнаружено, но оно может быть временным
                if current_time - self.last_motion_time > self.motion_cooldown:
                    # Проверяем, было ли движение достаточно длительным
                    if self.last_motion_time - self.motion_start_time >= self.min_motion_duration:
                        message = "Движение закончилось"
                        self.notify(message)
                        print("Движение закончилось.")
                    self.motion_active = False
                    self.motion_start_time = None
                    self.last_motion_time = None

        # Возвращаем обработанный кадр и флаг движения
        return frame, motion_detected
