from pydantic import BaseModel
from datetime import datetime, time
from typing import List, Optional
from enum import Enum



class JobTypeEnum(str,Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    one_time_project = "one_time_project"
    internship = "internship"

class WorkModeEnum(str,Enum):
    online = "online"
    offline = "offline"

class GigPost(BaseModel):
    gigs_title: str
    price: float
    duration: int
    description: str
    category_id:int
    job_type: JobTypeEnum  # Enum tipini qo'shish
    work_mode: WorkModeEnum  # Enum tipini qo'shish



class Gig(BaseModel):
    id: int
    gigs_title: str
    duration: int
    price: float
    description: str
    status:bool
    category_id:int
    user_id: int
    job_type: JobTypeEnum  # Enum tipini qo'shish
    work_mode: WorkModeEnum  # Enum tipini qo'shish



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
    job_type: JobTypeEnum  # Enum tipini qo'shish
    work_mode: WorkModeEnum  # Enum tipini qo'shish
 


class GigResponse(BaseModel):
    id: int
    gigs_title: str
    price: float
    duration: int
    description: str
    status: bool
    category_id: int
    user_id: int
    job_type: JobTypeEnum  # Enum tipini qo'shish
    work_mode: WorkModeEnum  # Enum tipini qo'shish
  


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
    job_type: JobTypeEnum  # Enum tipini qo'shish
    work_mode: WorkModeEnum  # Enum tipini qo'shish
    category: GigCategoryResponse
    tags: List[GigTagResponse]
    files: List[GigFileResponse]
    user_id: int

