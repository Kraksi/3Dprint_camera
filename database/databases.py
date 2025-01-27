from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from validation.all_classes import UserCreateSchema, UserUpdateSchema
from sqlalchemy.sql import text

# Базовый класс для моделей
Base = declarative_base()

"""
Класс DatabaseConnection для создания подключения к базе данных с использованием паттерна Singleton.
Singleton необходим для избежания дублирования при создании подключения к базе.
"""

class DatabaseConnection:
    # Использование паттерна Singleton
    _instance = None

    def __new__(cls, username, password, host, database):
        if not cls._instance:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, username, password, host, database):
        if not self._initialized:
            # Изменена строка подключения для использования pymysql
            self.database_url = f"mysql+pymysql://{username}:{password}@{host}/{database}"
            self.engine = create_engine(self.database_url, echo=True)
            self.SessionFactory = sessionmaker(bind=self.engine, expire_on_commit=False)
            self._initialized = True

    def get_session(self):
        return self.SessionFactory()

    def close_session(self):
        self.engine.dispose()

    def create_tables(self):
        with self.engine.begin() as conn:
            Base.metadata.create_all(conn)


# Создание таблицы пользователей
class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<User(username={self.username}, password={self.password})>"


# Создание таблицы информации о печати
class PrintInfo(Base):
    __tablename__ = 'print_info'

    id = Column(Integer, primary_key=True)
    print_time = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    image = Column(Text, nullable=True)

    def __repr__(self):
        return f"<PrintInfo(print_time={self.print_time}, status={self.status}, image={self.image})>"


"""
Использование паттерна репозиторий для упрощения использования информации, которая должна быть записана в базу.
Также позволяет использовать информацию в других местах при необходимости.
"""

class UserRepository:
    def __init__(self, session):
        self.session = session

    def add_user(self, user_data: UserCreateSchema):
        try:
            new_user = Users(username=user_data.username, password=user_data.password)
            self.session.add(new_user)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Ошибка добавления пользователя: {e}")

    def get_user(self, user_id):
        query = text("SELECT * FROM users WHERE id = :id")
        result = self.session.execute(query, {"id": user_id})
        return result.fetchone()

    def update_user(self, user_id, user_data: UserUpdateSchema):
        user = self.get_user(user_id)
        if user:
            if user_data.username:
                user.username = user_data.username
            if user_data.password:
                user.password = user_data.password
            self.session.commit()

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()


class PrintInfoRepository:
    def __init__(self, session):
        self.session = session

    def add_print_info(self, print_time, status, image=None):
        try:
            new_print_info = PrintInfo(print_time=print_time, status=status, image=image)
            self.session.add(new_print_info)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Ошибка добавления информации о печати: {e}")

    def get_print_info(self, print_time_id):
        query = text("SELECT * FROM print_info WHERE id = :id")
        result = self.session.execute(query, {"id": print_time_id})
        return result.fetchone()

    def update_print_info(self, print_time_id, status=None, image=None):
        print_info = self.get_print_info(print_time_id)
        if print_info:
            if status:
                print_info.status = status
            if image:
                print_info.image = image
            self.session.commit()

    def delete_print_info(self, print_time_id):
        print_info = self.get_print_info(print_time_id)
        if print_info:
            self.session.delete(print_info)
            self.session.commit()
