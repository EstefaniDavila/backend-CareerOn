from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import shutil
from core.supabase_db import get_db
from supabase import Client
from typing import Dict, Any
from api.dependencies.auth import get_current_user

router = APIRouter()

DEMO_EMAIL = "estefanidaviladev@gmail.com"

@router.get("/profile")
def get_student_profile():
    try:
        db: Client = get_db()
        
        user_resp = db.table("Usuario").select("*").eq("email", DEMO_EMAIL).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_data = user_resp.data[0]
        user_id = user_data["id"]
        
        exp_resp = db.table("Experience").select("*").eq("user_id", user_id).execute()
        experiences = exp_resp.data if exp_resp.data else []
        
        proj_resp = db.table("Project").select("*").eq("user_id", user_id).execute()
        projects = proj_resp.data if proj_resp.data else []
        
        skill_resp = db.table("UserSkill").select("level, Skill(name)").eq("user_id", user_id).execute()
        skills = skill_resp.data if skill_resp.data else []

        try:
            lang_resp = db.table("UserLanguage").select("level, Language(name)").eq("user_id", user_id).execute()
            languages = lang_resp.data if lang_resp.data else []
        except:
            languages = []
        
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
async def upload_resume(file: UploadFile = File(...)):
    try:
        db: Client = get_db()
        
        user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        user_id = user_resp.data[0]["id"]
        
        filename = file.filename
        file_location = f"uploads/{user_id}_{filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        file_url = f"http://localhost:8000/uploads/{user_id}_{filename}"
        
        db.table("Resume").update({"is_default": False}).eq("user_id", user_id).execute()
        
        new_resume = {
            "user_id": user_id,
            "title": f"CV Generado - {filename}",
            "file_url": file_url,
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

@router.delete("/project/{project_id}")
def delete_project(project_id: int, current_user: dict = Depends(get_current_user)):
    try:
        db: Client = get_db()
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data: 
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_id = user_resp.data[0]["id"]
        
        db.table("Project").delete().eq("id", project_id).eq("user_id", user_id).execute()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        print("Error eliminando proyecto:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

class SkillData(BaseModel):
    name: str
    level: str

@router.post("/skill")
def add_skill(data: SkillData):
    db: Client = get_db()
    user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
    if not user_resp.data: return {"status": "error"}
    user_id = user_resp.data[0]["id"]
    
    skill_resp = db.table("Skill").select("id").eq("name", data.name).execute()
    if not skill_resp.data:
        ins = db.table("Skill").insert({"name": data.name, "category": "General"}).execute()
        skill_id = ins.data[0]["id"]
    else:
        skill_id = skill_resp.data[0]["id"]
        
    db.table("UserSkill").insert({
        "user_id": user_id,
        "skill_id": skill_id,
        "level": data.level
    }).execute()
    return {"status": "success"}

@router.get("/jobs")
def get_all_jobs():
    """Obtiene todas las ofertas de trabajo activas para el feed del estudiante, incluyendo sus skills."""
    db: Client = get_db()
    try:
        # Filtramos por status = "publicada"
        jobs_resp = db.table("JobPost").select("*").eq("status", "publicada").execute()
        jobs = jobs_resp.data
        users_resp = db.table("Usuario").select("id, company_name").eq("type", "Recruiter").execute()
        recruiters = {u["id"]: u.get("company_name", "Empresa Confidencial") for u in users_resp.data}
        
        # Obtener todos los skills y requisitos para hacer el join en memoria (más rápido para hackathon)
        skills_resp = db.table("Skill").select("id, name").execute()
        skills_dict = {s["id"]: s["name"] for s in skills_resp.data}
        
        reqs_resp = db.table("JobRequirement").select("job_id, skill_id").execute()
        
        # Agrupar requirements por job_id
        job_skills_map = {}
        for req in reqs_resp.data:
            job_id = req["job_id"]
            skill_name = skills_dict.get(req["skill_id"])
            if skill_name:
                if job_id not in job_skills_map:
                    job_skills_map[job_id] = []
                job_skills_map[job_id].append(skill_name)
                
        # Obtener y contar postulaciones reales
        apps_resp = db.table("Application").select("job_id").execute()
        app_counts = {}
        for app in apps_resp.data:
            jid = app["job_id"]
            app_counts[jid] = app_counts.get(jid, 0) + 1
        
        formatted_jobs = []
        from datetime import datetime, timezone
        
        for j in jobs:
            # Calcular días desde la creación
            posted_days_ago = 0
            if j.get("created_at"):
                try:
                    created_date = datetime.fromisoformat(j["created_at"].replace("Z", "+00:00"))
                    posted_days_ago = (datetime.now(timezone.utc) - created_date).days
                except:
                    pass

            formatted_jobs.append({
                "id": j["id"],
                "title": j["title"],
                "company": recruiters.get(j["recruiter_id"], "Empresa Confidencial"),
                "location": j.get("location") or "Remoto", 
                "type": j.get("job_type") or "Tiempo completo",
                "description": j["description"],
                "skills_required": job_skills_map.get(j["id"], ["React", "CSS", "UI/UX"]),
                "posted_days_ago": max(posted_days_ago, 0),
                "applicants_count": app_counts.get(j["id"], 0), # Conteo 100% real
                "is_match": True,
                "salary_range": j.get("salary_range") or "No especificado",
            })
            
        return formatted_jobs
    except Exception as e:
        print("Error en /api/student/jobs:", e)
        return []

@router.post("/jobs/{job_id}/apply")
def apply_to_job(job_id: int, current_user: dict = Depends(get_current_user)):
    try:
        db: Client = get_db()

        user_resp = db.table("Usuario") \
            .select("id") \
            .eq("email", current_user["email"]) \
            .execute()

        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_id = user_resp.data[0]["id"]

        existing = db.table("Application") \
            .select("*") \
            .eq("job_id", job_id) \
            .eq("student_id", user_id) \
            .execute()

        if existing.data:
            raise HTTPException(
                status_code=400,
                detail="Ya has postulado a este empleo."
            )

        app_data = {
            "job_id": job_id,
            "student_id": user_id,
            "status": "Pendiente"
        }

        res = db.table("Application").insert(app_data).execute()

        return {
            "message": "Postulación enviada exitosamente",
            "data": res.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
