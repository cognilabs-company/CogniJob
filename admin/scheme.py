from pydantic import BaseModel
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
    is_admin: bool
