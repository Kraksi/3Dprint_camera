from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database.databases import DatabaseConnection, UserRepository, PrintInfoRepository
from validation.all_classes import LoginRequest
from functions.motiondetector import MotionDetector
from functions.errorsdetector import FindError
from connectors.videoconnect import VideoStream
from observer.notifier import ConsoleNotifier
import cv2
from decorators.decorators import TimerDetectorDecorator, PrintErrorDetector
from handlers.handlers import handle_motion_end, handle_print_error
from datetime import datetime

app = FastAPI(debug=True)
templates = Jinja2Templates(directory="templates")

# Глобальные переменные для статуса и времени печати
printing_status = "Ожидание начала печати"
motion_start_time = None
total_time = 0
streaming_active = True
last_frame = None

# Обработчик ошибок печати
printing_error = False
error_message = ""


def get_videostream():
    return VideoStream(0)


videostream = get_videostream()


def get_db():
    db = DatabaseConnection(
        username='krasti',
        password='Admin20)$1998',
        host='193.233.48.188',
        database='3dprint_base'
    )
    db.create_tables()
    session = db.get_session()
    return session


# Получение репозитория пользователя
def get_user_repo():
    db_session = get_db()
    return UserRepository(db_session)


def get_print_repo():
    db_session = get_db()
    return PrintInfoRepository(db_session)


@app.get("/", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user_repo = get_user_repo()
    login_data = LoginRequest(username=username, password=password)
    users = user_repo.get_all_users()
    for user in users:
        if user.username == login_data.username and user.password == login_data.password:
            return RedirectResponse(url="/status", status_code=303)

    return templates.TemplateResponse(request, "login.html", {
        "request": request,
        "message": "Неверный логин или пароль"
    })


@app.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    global printing_status, total_time
    return templates.TemplateResponse(request, "status.html", {
        "request": request,
        "status": printing_status,
        "elapsed_time": f"{total_time:.2f}"
    })


@app.get("/end_print", response_class=HTMLResponse)
def end_print_page(request: Request):
    return templates.TemplateResponse(
        request,
        "end_print.html",
        {
            "request": request,
            "status": printing_status,
            "elapsed_time": f"{total_time:.2f}",
            "error": printing_error,
        }
    )


@app.get("/stream", response_class=StreamingResponse)
def video_stream():
    global printing_status, motion_start_time, total_time, printing_error, error_message, streaming_active, last_frame, videostream

    detector = MotionDetector()
    find_error_detector = FindError(error_threshold=0)
    motion_timer_decorator = TimerDetectorDecorator(detector)
    print_error_detector = PrintErrorDetector(motion_timer_decorator, find_error_detector)

    # Инициализация наблюдателей
    console_notifier = ConsoleNotifier()
    motion_timer_decorator.attach(console_notifier)

    # Установка обработчиков событий
    def motion_end_handler(total_motion_time, last_frame):
        global printing_status, total_time, streaming_active

        print_repo = get_print_repo()
        handle_motion_end(total_motion_time, last_frame, print_repo)
        printing_status = "Печать завершена успешно"
        total_time = total_motion_time
        streaming_active = False  # Останавливаем стриминг

    def print_error_handler(elapsed_time, last_frame, error_message):
        global printing_status, printing_error, total_time, streaming_active

        print_repo = get_print_repo()
        handle_print_error(elapsed_time, last_frame, error_message, print_repo)
        printing_status = f"Ошибка: {error_message}"
        printing_error = True
        total_time = elapsed_time
        streaming_active = False  # Останавливаем стриминг

    motion_timer_decorator.set_motion_end_handler(motion_end_handler)
    print_error_detector.set_error_handler(print_error_handler)

    def frame_generator():
        global motion_start_time, printing_status, total_time, streaming_active, last_frame, videostream
        print_repo = get_print_repo()
        try:
            while streaming_active:
                try:
                    frame = videostream.get_frame()
                    if frame is None:
                        print("Ошибка: кадр не получен.")
                        break

                    print("Кадр получен успешно.")  # Отладочное сообщение

                    # Обработка кадра
                    result = print_error_detector.process_frame(frame)
                    processed_frame, motion_detected = result

                    # Обновление статуса и времени
                    if motion_detected and printing_status != "Идет печать":
                        motion_start_time = datetime.now()
                        printing_status = "Идет печать"

                    if motion_start_time is not None:
                        total_time = (datetime.now() - motion_start_time).total_seconds()
                    else:
                        total_time = 0

                    # Сжатие кадра в JPEG
                    ret, buffer = cv2.imencode('.jpg', processed_frame)
                    if not ret:
                        print("Ошибка: не удалось сжать кадр в JPEG.")
                        continue
                    frame_bytes = buffer.tobytes()

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                    last_frame = frame

                except ValueError as e:
                    print(f"Ошибка при получении кадра: {e}")
                    break
                except Exception as e:
                    print(f"Неожиданная ошибка при обработке кадра: {e}")
                    break

        except Exception as e:
            print(f"Ошибка во время обработки видео: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            total_motion_time = motion_timer_decorator.get_motion_time()
            if not printing_error:
                handle_motion_end(total_motion_time, last_frame, print_repo)
            videostream.release()

    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/resume")
def resume_processing():
    global streaming_active, printing_error, error_message, videostream
    streaming_active = True
    printing_error = False
    error_message = ""
    videostream = get_videostream()
    return JSONResponse(content={"message": "Обработка возобновлена."})


@app.get("/print_status")
def get_print_status():
    global printing_status, printing_error
    return JSONResponse(content={
        "status": printing_status,
        "error": printing_error
    })
