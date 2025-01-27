import cv2
import base64

async def handle_motion_end(total_motion_time, last_frame, print_repo):
    if last_frame is None:
        print("Ошибка: last_frame пустой или None.")
        return

    try:
        _, buffer = cv2.imencode('.jpg', last_frame)
        binary_frame = base64.b64encode(buffer).decode('utf-8')
    except cv2.error as e:
        print(f"Ошибка при кодировании кадра: {e}")
        return

    try:
        await print_repo.add_print_info(print_time=total_motion_time, status="Модель напечатана без ошибок", image=binary_frame)
        print("Данные о печати записаны в базу.")
    except Exception as e:
        print(f"Ошибка записи данных в базу: {e}")

async def handle_print_error(elapsed_time, last_frame, error_message, print_info_repo):
    """
    Асинхронная обработка ошибки печати и запись данных в базу.
    """
    # Проверка на пустой кадр
    if last_frame is None:
        print("Ошибка: last_frame пустой или None.")
        return

    try:
        # Конвертируем последний кадр в бинарный вид
        _, buffer = cv2.imencode('.jpg', last_frame)
        binary_frame = base64.b64encode(buffer).decode('utf-8')
    except cv2.error as e:
        print(f"Ошибка при кодировании кадра: {e}")
        return

    # Формируем статус с сообщением об ошибке
    status = f"Ошибка печати: {error_message}"

    try:
        # Асинхронная запись данных в базу
        await print_info_repo.add_print_info(print_time=elapsed_time, status=status, image=binary_frame)
        print(f"Данные об ошибке печати записаны в базу. Время: {elapsed_time:.2f} секунд")
    except Exception as e:
        print(f"Ошибка записи данных об ошибке печати в базу: {e}")