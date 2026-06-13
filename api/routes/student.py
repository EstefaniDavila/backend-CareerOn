from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from core.supabase_db import get_db
from supabase import Client
from typing import Dict, Any

router = APIRouter()

# En un entorno real usaríamos Depends(get_current_user).
# Para la demo usaremos el correo hardcodeado de Estefani o pasarlo como query.
DEMO_EMAIL = "estefanidaviladev@gmail.com"

@router.get("/profile")
def get_student_profile():
    try:
        db: Client = get_db()
        
        # 1. Obtener usuario
        user_resp = db.table("Usuario").select("*").eq("email", DEMO_EMAIL).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_data = user_resp.data[0]
        user_id = user_data["id"]
        
        # 2. Obtener experiencia
        exp_resp = db.table("Experience").select("*").eq("user_id", user_id).execute()
        experiences = exp_resp.data if exp_resp.data else []
        
        # 3. Obtener proyectos
        proj_resp = db.table("Project").select("*").eq("user_id", user_id).execute()
        projects = proj_resp.data if proj_resp.data else []
        
        # 4. Obtener Habilidades (Skills)
        skill_resp = db.table("UserSkill").select("level, Skill(name)").eq("user_id", user_id).execute()
        skills = skill_resp.data if skill_resp.data else []

        # 5. Obtener Idiomas (Languages) - Intentamos consultar la tabla Language o UserLanguage
        try:
            lang_resp = db.table("UserLanguage").select("level, Language(name)").eq("user_id", user_id).execute()
            languages = lang_resp.data if lang_resp.data else []
        except:
            languages = []
        
        # 6. Obtener CV (Resume)
        res_resp = db.table("Resume").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).limit(1).execute()
        current_cv = res_resp.data[0] if res_resp.data else None
        
        return {
            "status": "success",
            "data": {
                "user": user_data,
                "experiences": experiences,
                "projects": projects,
                "skills": skills,
                "languages": languages,
                "current_cv": current_cv
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume")
async def save_new_resume(file: UploadFile = File(...)):
    try:
        db: Client = get_db()
        
        user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        user_id = user_resp.data[0]["id"]
        
        # En producción subiríamos `file.file.read()` al Supabase Storage.
        # Para esta demo guardaremos un registro simulando el URL de subida.
        filename = file.filename
        
        # Simulamos una URL pública (en un entorno real viene de db.storage.from_("cvs").get_public_url)
        mock_file_url = f"https://carrer-on-storage.com/cvs/{user_id}/{filename}"
        
        # Opcionalmente, quitar is_default al CV anterior
        db.table("Resume").update({"is_default": False}).eq("user_id", user_id).execute()
        
        # Insertar nuevo
        new_resume = {
            "user_id": user_id,
            "title": f"CV Generado - {filename}",
            "file_url": mock_file_url,
            "is_default": True
        }
        inserted = db.table("Resume").insert(new_resume).execute()
        
        return {
            "status": "success",
            "message": "CV actualizado correctamente",
            "data": inserted.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExperienceData(BaseModel):
    company_name: str
    position: str
    employment_type: str
    start_date: str
    end_date: str
    description: str

@router.post("/experience")
def add_experience(data: ExperienceData):
    db: Client = get_db()
    user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
    if not user_resp.data: return {"status": "error"}
    user_id = user_resp.data[0]["id"]
    
    db.table("Experience").insert({
        "user_id": user_id,
        "company_name": data.company_name,
        "position": data.position,
        "employment_type": data.employment_type,
        "start_date": data.start_date,
        "end_date": data.end_date if data.end_date else None,
        "currently_working": False,
        "description": data.description
    }).execute()
    return {"status": "success"}

class ProjectData(BaseModel):
    title: str
    description: str
    repository_url: str

@router.post("/project")
def add_project(data: ProjectData):
    db: Client = get_db()
    user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
    if not user_resp.data: return {"status": "error"}
    user_id = user_resp.data[0]["id"]
    
    db.table("Project").insert({
        "user_id": user_id,
        "title": data.title,
        "description": data.description,
        "repository_url": data.repository_url
    }).execute()
    return {"status": "success"}

class SkillData(BaseModel):
    name: str
    level: str

@router.post("/skill")
def add_skill(data: SkillData):
    db: Client = get_db()
    user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
    if not user_resp.data: return {"status": "error"}
    user_id = user_resp.data[0]["id"]
    
    # 1. Buscar o crear el Skill en la tabla principal
    skill_resp = db.table("Skill").select("id").eq("name", data.name).execute()
    if not skill_resp.data:
        ins = db.table("Skill").insert({"name": data.name, "category": "General"}).execute()
        skill_id = ins.data[0]["id"]
    else:
        skill_id = skill_resp.data[0]["id"]
        
    # 2. Insertar en UserSkill
    db.table("UserSkill").insert({
        "user_id": user_id,
        "skill_id": skill_id,
        "level": data.level
    }).execute()
    return {"status": "success"}
