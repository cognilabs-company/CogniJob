from datetime import datetime
from enum import Enum
import re
from pydantic import BaseModel, EmailStr, validator, StrictStr
from typing import Optional


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    username: str
    registered_date: datetime
    is_seller: bool
    is_client: bool
    is_superuser: bool
    telegram_username:str
    phone_number:str



class SellerResponse(BaseModel):
    id: int
    user_id: int
    image_url: Optional[str]
    description: Optional[str]
    cv_url: Optional[str]
    birth_date: Optional[str]

class UserWithSellerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    registered_date: str
    is_seller: bool
    is_client: bool
    is_superuser: bool
    telegram_username: Optional[str]
    phone_number: Optional[str]
    seller: Optional[SellerResponse]

class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    is_seller: bool
    is_client: bool
    is_superuser:bool
    telegram_username: Optional[str]
    phone_number: StrictStr  

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



class GigCategoryPost(BaseModel):
    category_name: str   


class TagCreate(BaseModel):
    tag_name: str     



class SkillCreate1(BaseModel):
    skill_name: str  


class OccupCreate1(BaseModel):
    occup_name: str  

class SellerSkill(BaseModel):
    id: int
    skill_name: str        


class SellerOccupation(BaseModel):
    id: int
    occup_name: str         