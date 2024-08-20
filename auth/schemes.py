from datetime import datetime

from pydantic import BaseModel


class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password1: str
    password2: str
    is_seller: bool
    is_client: bool


class UserInDB(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    is_seller: bool
    is_client: bool
    is_superuser:bool


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    username: str
    registered_date: datetime
    is_seller: bool
    is_client: bool

