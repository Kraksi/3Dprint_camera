from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from database.databases import DatabaseConnection, UserRepository, PrintInfoRepository
from validation.all_classes import LoginRequest
from functions.motiondetector import MotionDetector
from functions.errorsdetector import FindError
from connectors.videoconnect import VideoStreamSingleton
from observer.notifier import ConsoleNotifier
import cv2
from decorators.decorators import TimerDetectorDecorator, PrintErrorDetector
from handlers.handlers import handle_motion_end, handle_print_error
from datetime import datetime
import asyncio

app = FastAPI(debug=True)
templates = Jinja2Templates(directory="templates")
rtsp_url = 'rtsp://krasti:anuBIS0431!@192.168.1.89:554/stream1'

# Глобальные переменные для статуса и времени печати
printing_status = "Ожидание начала печати"
motion_start_time = None
total_time = 0
streaming_active = True
last_frame = None

# Обработчик ошибок печати
printing_error = False
error_message = ""
videostream = VideoStreamSingleton(rtsp_url)

# Функция для получения сессии базы данных
async def get_db():
    db = DatabaseConnection(
        username='krasti',
        password='Admin20)$1998',
        host='193.233.48.188',
        database='3dprint_base'
    )
    await db.create_tables()
    session = await db.get_session()
    try:
        yield session
    finally:
        await session.close()

# Зависимости для правильно использования pytest
async def get_user_repo(db: AsyncSession = Depends(get_db)):
    return UserRepository(db)

async def get_print_repo(db: AsyncSession = Depends(get_db)):
    return PrintInfoRepository(db)

@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), user_repo: UserRepository = Depends(get_user_repo)):
    login_data = LoginRequest(username=username, password=password)
    user = await user_repo.get_user(1)

    if user.username != login_data.username:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Неверный логин"
        })
    elif user.password != login_data.password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Неверный пароль"
        })

    return RedirectResponse(url="/status", status_code=303)

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    global printing_status, total_time
    return templates.TemplateResponse("status.html", {
        "request": request,
        "status": printing_status,
        "elapsed_time": f"{total_time:.2f}"
    })

@app.get("/end_print", response_class=HTMLResponse)
async def end_print_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="end_print.html",
        context={
            "request": request,
            "status": printing_status,
            "elapsed_time": f"{total_time:.2f}",
            "error": printing_error,
        }
    )

@app.get("/stream", response_class=StreamingResponse)
async def video_stream(print_repo: PrintInfoRepository = Depends(get_print_repo)):
    global printing_status, motion_start_time, total_time, printing_error, error_message, streaming_active, last_frame

    detector = MotionDetector()
    find_error_detector = FindError(error_threshold=0)
    motion_timer_decorator = TimerDetectorDecorator(detector)
    print_error_detector = PrintErrorDetector(motion_timer_decorator, find_error_detector)

    # Инициализация наблюдателей
    console_notifier = ConsoleNotifier()
    motion_timer_decorator.attach(console_notifier)

    # Установка обработчиков событий
    async def motion_end_handler(total_motion_time, last_frame):
        global printing_status, total_time, streaming_active
        await handle_motion_end(total_motion_time, last_frame, print_repo)
        printing_status = "Печать завершена успешно"
        total_time = total_motion_time
        streaming_active = False  # Останавливаем стриминг
        return RedirectResponse(url="/end_print")

    async def print_error_handler(elapsed_time, last_frame, error_message):
        global printing_status, printing_error, total_time, streaming_active
        await handle_print_error(elapsed_time, last_frame, error_message, print_repo)
        printing_status = f"Ошибка: {error_message}"
        printing_error = True
        total_time = elapsed_time
        streaming_active = False  # Останавливаем стриминг
        return RedirectResponse(url="/end_print")

    motion_timer_decorator.set_motion_end_handler(motion_end_handler)
    print_error_detector.set_error_handler(print_error_handler)

    async def frame_generator():
        global motion_start_time, printing_status, total_time, streaming_active, last_frame

        try:
            while streaming_active:
                frame = videostream.get_frame()
                if frame is None:
                    print("Ошибка: кадр не получен.")
                    break

                print("Кадр получен успешно.")  # Отладочное сообщение

                # Обработка кадра
                result = await print_error_detector.process_frame(frame)
                processed_frame, motion_detected = result

                # Обновление статуса и времени
                if motion_detected and printing_status != "Printing in progress":
                    motion_start_time = datetime.now()
                    printing_status = "Printing in progress"

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

                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Ошибка во время обработки видео: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            total_motion_time = motion_timer_decorator.get_motion_time()
            if not printing_error:
                await handle_motion_end(total_motion_time, last_frame, print_repo)
            videostream.release()

    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/resume")
async def resume_processing():
    global streaming_active, printing_error, error_message
    streaming_active = True
    printing_error = False
    error_message = ""
    return JSONResponse(content={"message": "Обработка возобновлена."})