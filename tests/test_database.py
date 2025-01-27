import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.databases import Base, DatabaseConnection, Users, PrintInfo, UserRepository, PrintInfoRepository
from validation.all_classes import UserCreateSchema


@pytest.fixture
def db_connection():
    # Используем временную базу данных SQLite для тестов
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def test_database_connection(db_connection):
    db = DatabaseConnection(username='test', password='test', host='localhost', database='test')
    session = db.get_session()
    assert session is not None


def test_user_repository_add_user(db_connection):
    user_repo = UserRepository(db_connection)
    user_data = UserCreateSchema(username='testuser', password='testpass')  # Используем UserCreateSchema
    user_repo.add_user(user_data)
    user = db_connection.query(Users).filter_by(username='testuser').first()
    assert user is not None
    assert user.username == 'testuser'


def test_print_info_repository_add_print_info(db_connection):
    print_repo = PrintInfoRepository(db_connection)
    print_repo.add_print_info(print_time='10:00', status='success')
    print_info = db_connection.query(PrintInfo).filter_by(print_time='10:00').first()
    assert print_info is not None
    assert print_info.status == 'success'
