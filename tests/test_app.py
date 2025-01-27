import pytest
from fastapi.testclient import TestClient
from main.app import app
from database.databases import Base, Users
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_connection():
    # Используем временную базу данных SQLite для тестов
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def test_login_success(client, db_connection):
    # Добавляем тестового пользователя с ID=1 в базу данных
    user = Users(id=1, username='testuser', password='testpass')
    db_connection.add(user)
    db_connection.commit()

    response = client.post("/login", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200


def test_login_failure(client, db_connection):
    response = client.post("/login", data={"username": "wronguser", "password": "wrongpass"})
    assert response.status_code == 200
    assert "Неверный логин" in response.text


def test_status_page(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert "Ожидание начала печати" in response.text


def test_end_print_page(client):
    response = client.get("/end_print")
    assert response.status_code == 200
    assert "Ожидание начала печати" in response.text


def test_resume_processing(client):
    response = client.post("/resume")
    assert response.status_code == 200
    assert response.json() == {"message": "Обработка возобновлена."}
