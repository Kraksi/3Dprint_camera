from observer.observer import Subject
import cv2
import numpy as np


class FindError(Subject):
    def __init__(self, error_threshold=0.1):
        super().__init__()
        self.sift = cv2.SIFT_create()  # Инициализация SIFT
        self.bf = cv2.BFMatcher()  # Инициализация BFMatcher
        self.error_threshold = error_threshold  # Порог ошибки для остановки
        self.paused = False  # Флаг приостановки обработки

    def calculate_quality_coefficient(self, reference_image, printed_image):
        # Если обработка приостановлена, возвращаем нулевой коэффициент
        if self.paused:
            return 0.0

        keypoints1, descriptors1 = self.sift.detectAndCompute(reference_image, None)
        keypoints2, descriptors2 = self.sift.detectAndCompute(printed_image, None)

        if descriptors1 is None or descriptors2 is None:
            return 0.0

        matches = self.bf.knnMatch(descriptors1, descriptors2, k=2)

        good_matches = []
        for m, n in matches:
            if m and n:
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
            else:
                raise ValueError("Недостаточно совпадений")

        match_ratio = len(good_matches) / len(keypoints1) if len(keypoints1) > 0 else 0

        error_ratio = self.detect_print_errors(printed_image)

        if error_ratio < self.error_threshold:
            self.paused = True
            self.notify(f"Ошибка печати обнаружена: {error_ratio:.2f}. Обработка приостановлена.")

        quality_coefficient = match_ratio * (1 - error_ratio)

        return quality_coefficient

    def detect_print_errors(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        error_area = sum(cv2.contourArea(contour) for contour in contours)
        total_area = image.shape[0] * image.shape[1]
        error_ratio = error_area / total_area if total_area > 0 else 0

        return error_ratio

    def resume(self):
        self.paused = False
        self.notify("Обработка возобновлена.")
