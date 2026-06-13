from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

# ==========================================
# AUTH & ONBOARDING
# ==========================================
class LoginRequest(BaseModel):
    email: str
    name: str
    microsoft_id: str

class OnboardingStudentRequest(BaseModel):
    email: str
    career: str
    semester: int
    goal: str
    has_experience: bool = False
    experience_type: Optional[str] = None
    has_projects: bool = False
    target_company: Optional[str] = None
    interest_area: Optional[str] = None

class OnboardingRecruiterRequest(BaseModel):
    email: str
    company_name: str
    job_title: Optional[str] = None
    corporate_email: str

# ==========================================
# PERFIL DEL ESTUDIANTE (Tablas del Compañero)
# ==========================================
class ResumeBase(BaseModel):
    title: Optional[str] = None
    file_url: str
    is_default: bool = True

class ExperienceBase(BaseModel):
    company_name: str
    position: str
    employment_type: str
    start_date: date
    end_date: Optional[date] = None
    currently_working: bool = False
    description: Optional[str] = None

class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: date
    end_date: Optional[date] = None
    currently_studying: bool = False

class CertificationBase(BaseModel):
    name: str
    organization: str
    issue_date: date
    credential_url: Optional[str] = None

class ProjectBase(BaseModel):
    title: str
    description: str
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SkillBase(BaseModel):
    skill_id: int
    level: str

# ==========================================
# ESQUEMAS DE GAMIFICACIÓN Y MASCOTAS
# ==========================================
class PetResponse(BaseModel):
    id: int
    user_id: str
    name: str
    current_level: int
    experience_points: int
    stage_image_url: Optional[str] = None

class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    reward_coins: int
    reward_xp: int
    status: str  # Pending, Completed

# ==========================================
# ESQUEMAS DE RECLUTADOR (B2B)
# ==========================================
class JobPostCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = "Remoto"
    job_type: Optional[str] = "Tiempo completo"
    salary_range: Optional[str] = "No especificado"
    skills_required: List[int]  # IDs de las habilidades requeridas
    required_levels: List[str]  # Niveles exigidos, ej: ['Avanzado', 'Intermedio']

class SponsoredChallengeCreate(BaseModel):
    challenge_id: int
    job_id: Optional[int] = None
    max_winners: int = 5
    tokens_cost: int
    min_career_score: int = 60

class SponsorshipCreate(BaseModel):
    student_id: str
    job_id: Optional[int] = None
    sponsored_challenge_id: int

# ==========================================
# ESQUEMAS DE ESTUDIANTE
# ==========================================
class SkillCreate(BaseModel):
    name: str
    category: str

class UserSkillCreate(BaseModel):
    user_id: UUID
    skill_id: int
    level: str

class ExperienceCreate(BaseModel):
    user_id: UUID
    company_name: str
    position: str
    employment_type: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    currently_working: bool