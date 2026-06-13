from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from core.supabase_db import get_db
from api.dependencies.auth import get_current_user
from services.ia_service import analyze_gap_with_gemini, optimize_cv_with_gemini
from pydantic import BaseModel

router = APIRouter()

@router.get("/evaluate/{job_id}")
def evaluate_job_match(job_id: int, current_user: dict = Depends(get_current_user)):
    """
    El Coach Evolutivo (IA) evalúa en tiempo real si el estudiante es apto
    para esta vacante y le da recomendaciones personalizadas.
    """
    try:
        db: Client = get_db()
        
        # 1. Obtener perfil completo del estudiante
        user_resp = db.table("Usuario").select("id, name, career, current_cycle, headline").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        student = user_resp.data[0]
        
        # Opcional: Obtener skills del estudiante de 'user_skills'
        skills_resp = db.table("UserSkill").select("level, Skill(name)").eq("user_id", student["id"]).execute()
        student_skills = []
        if skills_resp.data:
            student_skills = [{"name": s["Skill"]["name"], "level": s["level"]} for s in skills_resp.data if s.get("Skill")]
            
        student_profile = {
            "name": student["name"],
            "career": student["career"],
            "semester": student["current_cycle"],
            "headline": student["headline"],
            "skills": student_skills
        }
        
        # 2. Obtener detalles de la oferta de trabajo
        job_resp = db.table("JobPost").select("title, description").eq("id", job_id).execute()
        if not job_resp.data:
            raise HTTPException(status_code=404, detail="Vacante no encontrada")
            
        job_info = job_resp.data[0]
        
        # Obtener los requerimientos del trabajo
        req_resp = db.table("JobRequirement").select("required_level, Skill(name)").eq("job_id", job_id).execute()
        job_requirements = []
        if req_resp.data:
            job_requirements = [{"name": r["Skill"]["name"], "level": r["required_level"]} for r in req_resp.data if r.get("Skill")]
            
        job_post_data = {
            "title": job_info["title"],
            "description": job_info["description"],
            "requirements": job_requirements
        }
        
        # 3. Mandar la data a la IA (Gemini)
        ia_analysis = analyze_gap_with_gemini(student_profile, job_post_data)
        
        return {
            "status": "success",
            "coach_analysis": ia_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CVRequest(BaseModel):
    cv_text: str

@router.post("/optimize-cv")
def optimize_cv(data: CVRequest, current_user: dict = Depends(get_current_user)):
    """
    Recibe el texto del CV del estudiante, lo analiza con Gemini y devuelve feedback
    estructurado y una propuesta de mejora.
    """
    try:
        if not data.cv_text or len(data.cv_text) < 10:
            raise HTTPException(status_code=400, detail="El texto del CV es muy corto o inválido.")
            
        analysis = optimize_cv_with_gemini(data.cv_text)
        
        return {
            "status": "success",
            "message": "CV analizado correctamente por el Coach Evolutivo.",
            "data": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
