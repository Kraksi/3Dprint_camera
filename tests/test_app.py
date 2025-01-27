import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock
from datetime import datetime

from main.app import app  # Импортируйте свой FastAPI app из соответствующего файла

# Мокирование зависимостей
@pytest.fixture
def mock_get_db():
    mock_db = MagicMock()
    return mock_db

@pytest.fixture
def mock_print_repo():
    mock_repo = MagicMock()
    return mock_repo

@pytest.fixture
def mock_video_stream():
    mock_stream = MagicMock()
    return mock_stream

@pytest.fixture
def client():
    # Создание клиента FastAPI для тестов
    with TestClient(app) as client:
        yield client

# Тестирование маршрута "/"
def test_login_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Введите логин" in response.text

# Тестирование маршрута "/login"
@pytest.mark.asyncio
async def test_login(client, mock_get_db, mock_print_repo):
    # Мокирование логина пользователя
    mock_user = MagicMock()
    mock_user.username = "krasti"
    mock_user.password = "admin"

    mock_get_db.return_value.get_user.return_value = mock_user

    response = client.post("/login", data={"username": "krasti", "password": "admin"})
    assert response.status_code == 302  # Проверка на редирект
    assert response.headers["location"] == "/status"

@pytest.mark.asyncio
async def test_login_invalid(client, mock_get_db, mock_print_repo):
    # Мокирование неверных данных для логина
    mock_user = MagicMock()
    mock_user.username = "krasti"
    mock_user.password = "admin"

    mock_get_db.return_value.get_user.return_value = mock_user

    response = client.post("/login", data={"username": "krasti", "password": "wrongpassword"})

    # Проверка на статус код 200 (если мы не делаем редирект, а показываем ошибку на той же странице)
    assert response.status_code == 200

    # Проверка, что ошибка "Неверный пароль" присутствует в ответе
    assert "Неверный пароль" in response.text

# Тестирование маршрута "/status"
def test_status_page(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert "Ожидание начала печати" in response.text  # Начальный статус печати

# Тестирование маршрута "/end_print"
@pytest.mark.asyncio
async def test_end_print_page(client):
    response = client.get("/end_print")
    assert response.status_code == 200
    assert "Ожидание начала печати" in response.text  # Печать завершена

# Тестирование маршрута "/stream"
@pytest.mark.asyncio
async def test_video_stream(client, mock_video_stream):
    # Мокируем видеопоток
    mock_video_stream.get_frame.return_value = b"frame_data"

    response = client.get("/stream")
    assert response.status_code == 200
    assert "multipart/x-mixed-replace" in response.headers["content-type"]

# Тестирование маршрута "/resume"
@pytest.mark.asyncio
async def test_resume_processing(client):
    response = client.post("/resume")
    assert response.status_code == 200
    assert "Обработка возобновлена" in response.text  # Проверяем сообщение о возобновлении

