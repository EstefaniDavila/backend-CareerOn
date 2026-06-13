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
        
        # Verificar que es Reclutador
        user_response = db.table("Usuario").select("id, company_name, job_title, type").eq("email", current_user["email"]).execute()
        if not user_response.data or user_response.data[0].get("user_type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Acceso denegado. No eres reclutador.")
            
        recruiter = user_response.data[0]
        
        # Obtener saldo de tokens
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
        db: Client = get_db()
        
        # 1. Obtener ID del reclutador
        user_resp = db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute()
        if not user_resp.data or user_resp.data[0].get("type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Solo reclutadores pueden publicar ofertas.")
            
        recruiter_id = user_resp.data[0]["id"]
        
        # 2. Insertar JobPost
        job_data = {
            "recruiter_id": recruiter_id,
            "title": data.title,
            "description": data.description,
            "is_active": True
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
    """Lista los trabajos que este reclutador ha publicado."""
    try:
        db: Client = get_db()
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        recruiter_id = user_resp.data[0]["id"]
        
        jobs_resp = db.table("JobPost").select("*").eq("recruiter_id", recruiter_id).execute()
        return {"status": "success", "jobs": jobs_resp.data}
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
