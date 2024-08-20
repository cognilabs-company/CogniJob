from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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



class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str    




class GigCategoryPost(BaseModel):
    category_name: str   



class TagCreate(BaseModel):
    tag_name: str     