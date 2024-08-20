from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ProjectSkillCreate(BaseModel):
    skill_name: str
    seller_project_id: int


class ProjectSkill(BaseModel):
    id: int
    skill_name: str
    seller_project_id: int

    class Config:
        orm_mode = True


class ProjectFileCreate(BaseModel):
    file_url: str
    seller_project_id: int


class ProjectFile(BaseModel):
    id: int
    file_url: str
    seller_project_id: int

    class Config:
        orm_mode = True


class SellerProjectCreate(BaseModel):
    title: str
    category: Optional[str]
    price: float
    delivery_days: int
    description: Optional[str]
    status: Optional[str]


class SellerProject(BaseModel):
    id: int
    title: str
    category: Optional[str]
    price: float
    delivery_days: int
    seller_id: Optional[int]  # Adjusted if `seller_id` is optional
    description: Optional[str]
    status: Optional[str]
    files: List[ProjectFile] = []
    skills: List[ProjectSkill] = []

    class Config:
        orm_mode = True


class UserProjects(BaseModel):
    user_id: int
    projects: List[SellerProject]

    class Config:
        orm_mode = True


class CertificateCreate(BaseModel):
    pdf_url: str


class Certificate(BaseModel):
    id: int
    pdf_url: str
    seller_id: Optional[int]  # Adjusted if `seller_id` is optional

    class Config:
        orm_mode = True


class LanguageCreate(BaseModel):
    lan_name: str


class Language(BaseModel):
    id: int
    lan_name: str
    # seller_id: Optional[int]  # Adjusted if `seller_id` is optional

    class Config:
        orm_mode = True


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
    # seller_id: Optional[int]  # Adjusted if `seller_id` is optional
    city: Optional[str]
    country: Optional[str]
    job_title: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True


class OccupationCreate(BaseModel):
    occup_name: str


class Occupation(BaseModel):
    id: int
    occup_name: str
    # seller_id: Optional[int]  # Adjusted if `seller_id` is optional

    class Config:
        orm_mode = True


class Seller(BaseModel):
    id: int
    user_id: int
    image_url: Optional[str]
    description: Optional[str]
    cv_url: Optional[str]
    birth_date: Optional[date]
    active_gigs: Optional[int]
    languages: List[Language] = []
    experiences: List[Experience] = []
    occupations: List[Occupation] = []
    certificates: List[Certificate] = []

    class Config:
        orm_mode = True
