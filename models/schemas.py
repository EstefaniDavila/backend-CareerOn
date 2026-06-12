from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    career: str
    semester: int
    skills: List[str]

class LoginRequest(BaseModel):
    email: str
    name: str
    microsoft_id: str

class OnboardingStudentRequest(BaseModel):
    email: str
    career: str
    semester: int
    goal: str  # "ppp", "pp", "first_job", "target_company", "switch_area", "startup"
    has_experience: bool = False
    experience_type: Optional[str] = None  # "work", "volunteering", "freelance"
    has_projects: bool = False
    target_company: Optional[str] = None
    interest_area: Optional[str] = None

class OnboardingRecruiterRequest(BaseModel):
    email: str
    company_name: str
    job_title: Optional[str] = None
    corporate_email: str
