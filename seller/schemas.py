from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class SellerUpdateSchema(BaseModel):
    description: Optional[str] = None
    birth_date: date


class Profil(BaseModel):
    id:int
    description:str
    birth_date:date
    user_id:int





class ProjectSkillCreate(BaseModel):
    skill_name: str
    seller_project_id: int


class ProjectSkill(BaseModel):
    id: int
    skill_name: str
    seller_project_id: int




class ProjectFileCreate(BaseModel):
    file_url: str
    seller_project_id: int


class ProjectFile(BaseModel):
    id: int
    file_url: str
    seller_project_id: int



class SellerProjectCreate(BaseModel):
    title: str
    price: float
    delivery_days: int
    description: Optional[str]



class SellerProject(BaseModel):
    id: int
    title: str
    price: float
    delivery_days: int
    seller_id: Optional[int]  
    description: Optional[str]
    status: bool
    files: List[ProjectFile] = []




class UserProjects(BaseModel):
    user_id: int
    projects: List[SellerProject]

   




class Certificate(BaseModel):
    id: int
    pdf_url: str
    seller_id: Optional[int]  




class ExperienceCreate(BaseModel):
    company_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    city: Optional[str]
    country: Optional[str]
    job_title: Optional[str]
    description: Optional[str]


class Experience(BaseModel):
    id: int
    company_name: str
    start_date: Optional[date]
    end_date: Optional[date] 
    city: Optional[str]
    country: Optional[str]
    job_title: Optional[str]
    description: Optional[str]



class OccupationCreate(BaseModel):
    occup_name: str


class Occupation(BaseModel):
    id: int
    occup_name: str
 


class Seller(BaseModel):
    id: int
    user_id: int
    image_url: Optional[str]
    description: Optional[str]
    cv_url: Optional[str]
    birth_date: Optional[date]
    active_gigs: Optional[int]
    experiences: List[Experience] = []
    occupations: List[Occupation] = []
    certificates: List[Certificate] = []
