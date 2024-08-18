from pydantic import BaseModel
from datetime import datetime, time
from typing import List, Optional


class GigPost(BaseModel):
    gigs_title: str
    price: float
    duration: int
    description: str


class Gig(BaseModel):
    id: int
    gigs_title: str
    duration: int
    price: float
    description: str
    user_id: int


class GigCategoryPost(BaseModel):
    category_name: str
    gigs_id: int


class GigSkillPost(BaseModel):
    skill_name: str
    gigs_id: int


class GigFilePost(BaseModel):
    file_url: str
    gigs_id: int


class GigFile(BaseModel):
    id: int
    file_url: str
    gigs_id: int


class GigCategory(BaseModel):
    id: int
    category_name: str
    gigs_id: int


class GigSkill(BaseModel):
    id: int
    skill_name: str
    gigs_id: int


class GigCategoryfull(BaseModel):
    id: int
    category_name: str


class GigSkillfull(BaseModel):
    id: int
    skill_name: str


class GigFilefull(BaseModel):
    id: int
    file_url: str


class Gigfull(BaseModel):
    id: int
    gigs_title: str
    duration: Optional[int] = None
    price: float
    description: Optional[str] = None
    user_id: int
    categories: List[GigCategoryfull] = []
    skills: List[GigSkillfull] = []
    files: List[GigFilefull] = []