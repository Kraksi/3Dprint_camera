from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, Text
from validation.all_classes import UserCreateSchema, UserUpdateSchema
from sqlalchemy.sql import text
import asyncio

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
            self.database_url = f"mysql+asyncmy://{username}:{password}@{host}/{database}"
            self.engine = create_async_engine(self.database_url, echo=True)
            self.SessionFactory = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
            self._initialized = True

    async def get_session(self):
        return self.SessionFactory()

    async def close_session(self):
        await self.engine.dispose()

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


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

    async def add_user(self, user_data: UserCreateSchema):
        try:
            new_user = Users(username=user_data.username, password=user_data.password)
            self.session.add(new_user)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"Ошибка добавления пользователя: {e}")

    async def get_user(self, user_id):
        query = text("SELECT * FROM users WHERE id = :id")
        result = await self.session.execute(query, {"id": user_id})
        return result.fetchone()

    async def update_user(self, user_id, user_data: UserUpdateSchema):
        user = await self.get_user(user_id)
        if user:
            if user_data.username:
                user.username = user_data.username
            if user_data.password:
                user.password = user_data.password
            await self.session.commit()

    async def delete_user(self, user_id):
        user = await self.get_user(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()


class PrintInfoRepository:
    def __init__(self, session):
        self.session = session

    async def add_print_info(self, print_time, status, image=None):
        try:
            new_print_info = PrintInfo(print_time=print_time, status=status, image=image)
            self.session.add(new_print_info)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"Ошибка добавления информации о печати: {e}")

    async def get_print_info(self, print_time_id):

        query = text("SELECT * FROM users WHERE id = :id")
        result = await self.session.execute(query, {"id": print_time_id})
        return result.fetchone()

    async def update_print_info(self, print_time_id, status=None, image=None):
        print_info = await self.get_print_info(print_time_id)
        if print_info:
            if status:
                print_info.status = status
            if image:
                print_info.image = image
            await self.session.commit()

    async def delete_print_info(self, print_time_id):
        print_info = await self.get_print_info(print_time_id)
        if print_info:
            await self.session.delete(print_info)
            await self.session.commit()