from datetime import datetime

from pydantic import BaseModel
from typing import Optional

from pydantic import BaseModel, EmailStr, validator, constr
from pydantic import BaseModel, EmailStr, validator, StrictStr
from typing import Optional
import re
from pydantic import BaseModel, EmailStr, validator, StrictStr
from typing import Optional
import re

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    password1: str
    password2: str
    is_seller: bool
    is_client: bool
    telegram_username: Optional[str]
    phone_number: StrictStr  # telefon raqamini string sifatida qabul qilamiz

    @validator('telegram_username')
    def check_telegram_username(cls, v):
        if v and not v.startswith('@'):
            raise ValueError('Telegram username must start with "@"')
        return v

    @validator('phone_number')
    def check_phone_number(cls, v):
        if not re.match(r'^\+998\d{9}$', v):
            raise ValueError('Telefon raqami +998 bilan boshlanishi va 9 ta raqamni o‘z ichiga olishi kerak.')
        return v


class UserInDB(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    is_seller: bool
    is_client: bool
    is_superuser:bool
    telegram_username:str
    phone_number:str


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
    

