from pydantic import BaseModel, Field, validator
from typing import Optional


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)


class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50,
                          description="Имя пользователя должно быть уникальным и содержать от 3 до 50 символов.")
    password: str = Field(..., min_length=6, max_length=100,
                          description="Пароль должен содержать от 6 до 100 символов.")


class UserUpdateSchema(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50,
                                    description="Имя пользователя должно быть уникальным и содержать от 3 до 50 "
                                                "символов.")
    password: Optional[str] = Field(None, min_length=6, max_length=100,
                                    description="Пароль должен содержать от 6 до 100 символов.")
