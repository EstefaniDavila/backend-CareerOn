from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from core.supabase_db import get_db
from models.schemas import JobPostCreate
from api.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/dashboard")
def get_recruiter_dashboard(current_user: dict = Depends(get_current_user)):
    """Obtiene los datos clave del reclutador: su empresa y su saldo de tokens."""
    try:
        db: Client = get_db()
        
        user_response = db.table("Usuario").select("id, company_name, job_title, type").eq("email", current_user["email"]).execute()
        if not user_response.data or user_response.data[0].get("user_type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Acceso denegado. No eres reclutador.")
        recruiter = user_response.data[0]
        token_response = db.table("CompanyTokenPool").select("total_tokens_available").eq("recruiter_id", recruiter["id"]).execute()
        tokens = 0
        if token_response.data:
            tokens = token_response.data[0]["total_tokens_available"]
            
        return {
            "status": "success",
            "recruiter_info": {
                "company_name": recruiter.get("company_name"),
                "job_title": recruiter.get("job_title"),
                "tokens_available": tokens
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs")
def create_job_post(data: JobPostCreate, current_user: dict = Depends(get_current_user)):
    """Publica una nueva oferta de trabajo con sus habilidades requeridas."""
    try:
        from datetime import datetime, timedelta
        db: Client = get_db()
        
        # 1. Obtener ID del reclutador
        user_resp = db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute()
        if not user_resp.data or user_resp.data[0].get("type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Solo reclutadores pueden publicar ofertas.")
            
        recruiter_id = user_resp.data[0]["id"]
        
        # Generar deadline (3 días en el futuro) si no viene en el payload
        if data.deadline:
            future_date = data.deadline
        else:
            future_date = (datetime.now() + timedelta(days=3)).isoformat()
        
        # 2. Insertar JobPost
        job_data = {
            "recruiter_id": recruiter_id,
            "title": data.title,
            "description": data.description,
            "location": data.location,
            "job_type": data.job_type,
            "salary_range": data.salary_range,
            "is_active": True,
            "status": "publicada",
            "deadline": future_date
        }
        job_resp = db.table("JobPost").insert(job_data).execute()
        new_job_id = job_resp.data[0]["id"]
        
        # 3. Insertar Skills requeridos (JobRequirements)
        requirements = []
        for i, skill_id in enumerate(data.skills_required):
            # Asumimos que los levels vienen en el mismo orden
            req_level = data.required_levels[i] if i < len(data.required_levels) else "Intermedio"
            requirements.append({
                "job_id": new_job_id,
                "skill_id": skill_id,
                "required_level": req_level
            })
            
        if requirements:
            db.table("JobRequirement").insert(requirements).execute()
            
        return {
            "status": "success", 
            "message": "Oferta de trabajo publicada con éxito.",
            "job_id": new_job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs")
def list_my_jobs(current_user: dict = Depends(get_current_user)):
    """Lista los trabajos que este reclutador ha publicado, incluyendo habilidades, requisitos y cantidad de postulantes."""
    try:
        db: Client = get_db()
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        recruiter_id = user_resp.data[0]["id"]
        
        jobs_resp = db.table("JobPost").select("*").eq("recruiter_id", recruiter_id).execute()
        jobs = jobs_resp.data if jobs_resp.data else []
        
        if not jobs:
            return {"status": "success", "jobs": []}
            
        # Obtener los requerimientos para los trabajos del reclutador
        job_ids = [j["id"] for j in jobs]
        reqs_resp = db.table("JobRequirement").select("job_id, skill_id, required_level").in_("job_id", job_ids).execute()
        reqs = reqs_resp.data if reqs_resp.data else []
        
        # Obtener nombres de las habilidades
        skill_ids = list(set(r["skill_id"] for r in reqs))
        if skill_ids:
            skills_resp = db.table("Skill").select("id, name").in_("id", skill_ids).execute()
            skills_dict = {s["id"]: s["name"] for s in skills_resp.data}
        else:
            skills_dict = {}
            
        # Agrupar habilidades por job_id
        job_skills_map = {}
        for req in reqs:
            jid = req["job_id"]
            skill_obj = {
                "id": req["skill_id"],
                "name": skills_dict.get(req["skill_id"], "Desconocido"),
                "level": req["required_level"] or "Intermedio"
            }
            if jid not in job_skills_map:
                job_skills_map[jid] = []
            job_skills_map[jid].append(skill_obj)
            
        # Obtener y contar postulaciones reales para estos trabajos
        app_counts = {}
        try:
            apps_resp = db.table("Application").select("job_id").in_("job_id", job_ids).execute()
            if apps_resp.data:
                for app in apps_resp.data:
                    jid = app["job_id"]
                    app_counts[jid] = app_counts.get(jid, 0) + 1
        except Exception as e:
            print("Error counting applications for recruiter jobs:", e)
            
        # Agregar habilidades y conteo de postulantes a cada trabajo
        for j in jobs:
            j["skills"] = job_skills_map.get(j["id"], [])
            j["applicants_count"] = app_counts.get(j["id"], 0)
            
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/candidates")
def get_job_candidates(job_id: int, current_user: dict = Depends(get_current_user)):
    """Matchmaking Básico: Obtiene los estudiantes de la base de datos para una oferta."""
    try:
        db: Client = get_db()
        # En un sistema real complejo, aquí se ejecutaría el modelo Random Forest o un query SQL pesado.
        # Por ahora, para la Hackathon, listamos todos los estudiantes activos como mock de candidatos.
        students_resp = db.table("Usuario").select("id, name, career, current_cycle, headline").eq("type", "Student").execute()
        
        return {
            "status": "success",
            "message": "Candidatos obtenidos exitosamente",
            "candidates": students_resp.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from models.schemas import SponsoredChallengeCreate

@router.post("/sponsor")
def sponsor_challenge(data: SponsoredChallengeCreate, current_user: dict = Depends(get_current_user)):
    """El reclutador gasta sus tokens para abrir un Reto Patrocinado con cupos limitados."""
    try:
        db: Client = get_db()
        
        # 1. Obtener ID del reclutador
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        recruiter_id = user_resp.data[0]["id"]
        
        # 2. Verificar saldo de tokens
        pool_resp = db.table("CompanyTokenPool").select("total_tokens_available").eq("recruiter_id", recruiter_id).execute()
        if not pool_resp.data:
            raise HTTPException(status_code=400, detail="No tienes una cuenta de tokens B2B.")
            
        current_tokens = pool_resp.data[0]["total_tokens_available"]
        
        if current_tokens < data.tokens_cost:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Tienes {current_tokens} tokens y necesitas {data.tokens_cost}.")
            
        # 3. Descontar Tokens
        new_balance = current_tokens - data.tokens_cost
        db.table("CompanyTokenPool").update({"total_tokens_available": new_balance}).eq("recruiter_id", recruiter_id).execute()
        
        # 4. Crear el SponsoredChallenge
        sponsored_data = {
            "recruiter_id": recruiter_id,
            "challenge_id": data.challenge_id,
            "job_id": data.job_id,
            "max_winners": data.max_winners,
            "tokens_cost": data.tokens_cost,
            "min_career_score": data.min_career_score
        }
        resp = db.table("SponsoredChallenge").insert(sponsored_data).execute()
        
        return {
            "status": "success",
            "message": f"Reto patrocinado abierto para {data.max_winners} ganadores. Se descontaron {data.tokens_cost} tokens.",
            "new_balance": new_balance,
            "sponsored_challenge": resp.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
