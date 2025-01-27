from abc import ABC, abstractmethod
from typing import Optional, Callable

from observer.observer import Subject
from datetime import datetime
from functions.errorsdetector import FindError
import cv2


# Базовый класс декораторов
class DetectorDecorator(Subject, ABC):
    def __init__(self, detector: Subject):
        super().__init__()
        self._detector = detector

    def attach(self, observer):
        self._detector.attach(observer)

    def detach(self, observer):
        self._detector.detach(observer)

    def notify(self, message: str):
        self._detector.notify(message)

    @abstractmethod
    def process_frame(self, frame):
        pass


"""

TimerDetectorDecorator декоратор для расчета общего времени печати, сохранения последнего фрейма и последующей
загрузки этой информации в базу данных

"""


class TimerDetectorDecorator(DetectorDecorator):
    def __init__(self, detector: Subject, motion_cooldown: float = 10.0):
        super().__init__(detector)
        self.motion_start_time = None  # Время начала движения
        self.total_motion_time = 0  # Общее время движения
        self.last_frame = None  # Последний кадр при движении
        self.on_motion_end: Optional[Callable] = None  # Обработчик завершения движения
        self.motion_cooldown = motion_cooldown  # Время "охлаждения" перед завершением движения
        self.last_motion_time = None  # Время последнего обнаруженного движения

    def process_frame(self, frame):
        # Обработка кадра базовым детектором
        result = self._detector.process_frame(frame)
        processed_frame, motion_detected = result

        current_time = datetime.now()

        # Обработка обнаружения движения
        if motion_detected:
            if self.motion_start_time is None:
                # Движение началось
                self.motion_start_time = current_time
                print("MotionTimerDecorator: Движение началось.")
            self.last_motion_time = current_time  # Обновляем время последнего движения
            self.last_frame = frame
        else:
            if self.motion_start_time is not None:
                # Движение не обнаружено, но оно может быть временным
                if (current_time - self.last_motion_time).total_seconds() > self.motion_cooldown:
                    # Движение завершено
                    elapsed_time = (self.last_motion_time - self.motion_start_time).total_seconds()
                    self.total_motion_time += elapsed_time
                    self.motion_start_time = None  # Сбрасываем начальное время
                    self.last_motion_time = None

                    if self.on_motion_end:
                        self.on_motion_end(
                            self.total_motion_time,
                            self.last_frame if self.last_frame is not None else frame
                        )
                        print("MotionTimerDecorator: Движение завершено.")

        return processed_frame, motion_detected

    def set_motion_end_handler(self, handler: Callable):
        self.on_motion_end = handler

    def get_motion_time(self):
        return self.total_motion_time


"""

PrintErrorDetector декоратор для регистарции ошибки печати. Производит расчет общего времени печати до ошибки,
сохраненяет последний фрейм, ошибку для последующей записи информации в базу данных.

"""


class PrintErrorDetector(DetectorDecorator):
    def __init__(self, detector: Subject, error_detector: FindError, quality_threshold: float = 0.01):
        super().__init__(detector)
        self.print_start_time = datetime.now()
        self.error_occurred = False  # Флаг ошибки
        self.last_frame = None  # Последний фрейм с фиксацией ошибки
        self.on_error_handler = None  # Обработчик для ошибок печати
        self.error_detector = error_detector  # Объект для поиска ошибок
        self.quality_threshold = quality_threshold  # Порог для определения ошибки

    def process_frame(self, frame):
        try:
            # Обработка кадра основным детектором
            result = self._detector.process_frame(frame)
            processed_frame, motion_detected = result

            self.last_frame = frame

            # Вычисление коэффициента качества для текущего кадра
            reference_image = self.get_reference_image()
            quality_coefficient = self.error_detector.calculate_quality_coefficient(reference_image, frame)

            # Проверка на ошибку печати
            if quality_coefficient <= self.quality_threshold:
                self.error_occurred = True
                if self.print_start_time is not None:
                    elapsed_time = (datetime.now() - self.print_start_time).total_seconds()
                else:
                    elapsed_time = 0

                # Передача в хендлер для записи в базу
                if self.on_error_handler:
                    self.on_error_handler(elapsed_time, self.last_frame,
                                           f"Ошибка печати.\nКоэфициент схожести = {quality_coefficient:.2f}")

            return processed_frame, motion_detected

        except Exception as e:
            self.error_occurred = True
            elapsed_time = (datetime.now() - self.print_start_time).total_seconds()
            if self.on_error_handler:
                self.on_error_handler(elapsed_time, self.last_frame, str(e))
            raise e

    # Хендлер обрабатывающий ошибку
    def set_error_handler(self, handler):
        self.on_error_handler = handler

    # Загрузка эталонного изображения
    def get_reference_image(self):
        return cv2.imread("C../../referenceses/image2.jpg")
