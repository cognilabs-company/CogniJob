from pydantic import BaseModel
from datetime import datetime, time
from typing import List, Optional



class GigPost(BaseModel):
    gigs_title: str
    price: float
    duration: int
    description: str
    category_id:int


class Gig(BaseModel):
    id: int
    gigs_title: str
    duration: int
    price: float
    description: str
    status:bool
    category_id:int
    user_id: int


class GigStatus(BaseModel):
    status:bool
 

class GigTag(BaseModel):
    id: int
    tag_name: str


class GigFilePost(BaseModel):
    file_url: str
    gigs_id: int


class GigFilePostPut(BaseModel):
    file_url: str


class GigFile(BaseModel):
    id:int
    file_url: str
    gigs_id: int


class GigCategory(BaseModel):
    id:int
    category_name: str
    

class GigTagfull(BaseModel):
    id: int
    tag_name: str


class GigCategoryfull(BaseModel):
    id: int
    category_name: str


class GigFilefull(BaseModel):
    id: int
    file_url: str


class Gigfull(BaseModel):
    id: int
    gigs_title: str
    duration: int
    price: float
    description: str
    user_id: int
    categories: List[GigCategoryfull]
    tags: List[GigTagfull]
    files: List[GigFilefull]


class GigResponse(BaseModel):
    id: int
    gigs_title: str
    price: float
    duration: int
    description: str
    status: bool
    category_id: int
    user_id: int


class GigCategoryBase(BaseModel):
    category_name: str    


class GigSkillPostPut(BaseModel):
    skill_name: str    


class GigCategoryResponse(BaseModel):
    id: int
    category_name: str    


class GigFileResponse(BaseModel):
    id: int
    file_url: str


class GigTagResponse(BaseModel):
    id: int
    tag_name: str


class GigCategoryResponse(BaseModel):
    id: int
    category_name: str


class GigResponsesearch(BaseModel):
    id: int
    gigs_title: str
    duration: int
    price: float
    description: str
    status: bool
    category: GigCategoryResponse
    tags: List[GigTagResponse]
    files: List[GigFileResponse]
    user_id: int
