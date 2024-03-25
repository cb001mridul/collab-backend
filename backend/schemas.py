from typing import Optional,List
from pydantic import BaseModel,EmailStr
from sqlalchemy import Boolean, Column, Integer, String, Float,ARRAY
from datetime import datetime,date


class UserDisplay(BaseModel):

    id: int
    email: EmailStr


class UploadExp(BaseModel):

    company_name: str
    position: str
    description: str
    location: str
    start_date: date
    end_date: date


class UploadEdu(BaseModel):

    institute: str
    degree: str
    description: str
    location: str
    start_date: date
    end_date: str


class UploadAdmin(BaseModel):
    
    name: str
    description: str
    profile_fic: str
    educations: List[UploadEdu]
    experiences: List[UploadExp]  # List of experience IDs (integers)
    created_at: datetime
    updated_at: datetime
    is_active: bool
    user_id: int


class UploadContributor(BaseModel):

    name: str
    phone_number: str
    role: str
    stack: List[str]
    bio: str
    profile_pic: str
    experiences: List[UploadExp]
    educations: List[UploadEdu]
    created_at: datetime
    updated_at : datetime

    user_id: int



class ProjectUpload(BaseModel):

    title: str
    subtitle: str
    description: str
    tech_used: List[str]
    domain: List[str]
    contributors_active: int
    contributors_needed: int
    date_started: date

    user_id: int



class Token(BaseModel):

    access_token: str
    token_type: str


class TokenData(BaseModel):

    id: Optional[str] = None
    email: EmailStr



class UserUpload(BaseModel):

    organisation: str
    email: EmailStr
    name: str
    password: str
    is_admin: bool
    is_contributor: bool


class Apply(BaseModel):

    contributor_id: int