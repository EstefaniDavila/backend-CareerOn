from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from core.supabase_db import get_db
from models.schemas import JobPostCreate
from api.dependencies.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

@router.get("/dashboard")
def get_recruiter_dashboard(current_user: dict = Depends(get_current_user)):
    """Obtiene los datos clave del reclutador: su empresa y su saldo de tokens."""
    try:
        db: Client = get_db()
        
        user_response = db.table("Usuario").select("id, company_name, job_title, type").eq("email", current_user["email"]).execute()
        if not user_response.data or user_response.data[0].get("type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Acceso denegado. No eres reclutador.")
        recruiter = user_response.data[0]
        token_response = db.table("CompanyTokenPool").select("total_tokens_available").eq("recruiter_id", recruiter["id"]).execute()
        tokens = 0
        if token_response.data:
            tokens = token_response.data[0]["total_tokens_available"]
            
        # Obtener trabajos del reclutador
        jobs_resp = db.table("JobPost").select("id, is_active, status").eq("recruiter_id", recruiter["id"]).execute()
        jobs = jobs_resp.data if jobs_resp.data else []
        
        job_ids = [j["id"] for j in jobs]
        active_jobs_count = sum(1 for j in jobs if j.get("is_active") or j.get("status") in ["publicada", "published"])
        
        total_applicants = 0
        in_process_count = 0
        recent_activities = []
        ia_insight = None

        if job_ids:
            try:
                # Obtener postulaciones para conteos
                apps_resp = db.table("Application").select("id, status").in_("job_id", job_ids).execute()
                if apps_resp.data:
                    apps = apps_resp.data
                    total_applicants = len(apps)
                    # Consideramos en proceso cualquier estado que indique avance (ej: Entrevista, Prueba)
                    in_process_count = sum(1 for a in apps if str(a.get("status", "")).lower() in ["entrevista", "interview", "en proceso", "review", "en revision"])

                # Obtener postulaciones recientes con detalles (limitamos a 3)
                recent_resp = db.table("Application").select("id, status, created_at, student_id, job_id, Usuario(name), JobPost(title)").in_("job_id", job_ids).order("created_at", desc=True).limit(3).execute()
                if recent_resp.data:
                    for app in recent_resp.data:
                        student_name = app.get("Usuario", {}).get("name", "Candidato") if app.get("Usuario") else "Candidato"
                        job_title = app.get("JobPost", {}).get("title", "Oferta") if app.get("JobPost") else "Oferta"
                        created_at = app.get("created_at")
                        recent_activities.append({
                            "id": app["id"],
                            "student_name": student_name,
                            "job_title": job_title,
                            "status": app.get("status", "Pendiente"),
                            "created_at": created_at
                        })
                    
                    # Generar un Insight IA mock basado en la última postulación
                    last_app = recent_activities[0]
                    ia_insight = {
                        "title": "Insight IA",
                        "message": f"**{last_app['student_name']}** es un candidato fuerte para **{last_app['job_title']}** basado en un análisis de compatibilidad (95% de match) con los requisitos del puesto."
                    }

            except Exception as e:
                print("Error fetching applications for dashboard:", e)
            
        return {
            "status": "success",
            "recruiter_info": {
                "company_name": recruiter.get("company_name"),
                "job_title": recruiter.get("job_title"),
                "tokens_available": tokens
            },
            "active_jobs_count": active_jobs_count,
            "total_applicants": total_applicants,
            "in_process_count": in_process_count,
            "recent_activities": recent_activities,
            "ia_insight": ia_insight
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


@router.put("/jobs/{job_id}")
def update_job_post(
    job_id: int,
    data: JobPostCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute())

        if not user_resp.data or user_resp.data[0].get("type") != "Recruiter":
            raise HTTPException(
                status_code=403,
                detail="Solo reclutadores pueden editar ofertas."
            )

        recruiter_id = user_resp.data[0]["id"]

        job_resp = (
            db.table("JobPost")
            .select("id")
            .eq("id", job_id)
            .eq("recruiter_id", recruiter_id)
            .execute()
        )

        if not job_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Oferta no encontrada."
            )

        db.table("JobPost").update({
            "title": data.title,
            "description": data.description,
            "location": data.location,
            "job_type": data.job_type,
            "salary_range": data.salary_range
        }).eq("id", job_id).execute()

        db.table("JobRequirement").delete().eq(
            "job_id",
            job_id
        ).execute()

        requirements = []

        for i, skill_id in enumerate(data.skills_required):
            req_level = (
                data.required_levels[i]
                if i < len(data.required_levels)
                else "Intermedio"
            )

            requirements.append({
                "job_id": job_id,
                "skill_id": skill_id,
                "required_level": req_level
            })

        if requirements:
            db.table("JobRequirement").insert(
                requirements
            ).execute()

        return {
            "status": "success",
            "message": "Oferta actualizada correctamente."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@router.delete("/jobs/{job_id}")
def delete_job_post(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute())

        if not user_resp.data or user_resp.data[0]["type"] != "Recruiter":
            raise HTTPException(
                status_code=403,
                detail="Solo reclutadores pueden eliminar ofertas."
            )

        recruiter_id = user_resp.data[0]["id"]

        job_resp = (
            db.table("JobPost")
            .select("id")
            .eq("id", job_id)
            .eq("recruiter_id", recruiter_id)
            .execute()
        )

        if not job_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Oferta no encontrada."
            )

        db.table("JobRequirement") \
            .delete() \
            .eq("job_id", job_id) \
            .execute()

        db.table("SponsoredChallenge") \
            .delete() \
            .eq("job_id", job_id) \
            .execute()

        db.table("Application") \
            .delete() \
            .eq("job_id", job_id) \
            .execute()

        db.table("JobPost") \
            .delete() \
            .eq("id", job_id) \
            .execute()

        return {
            "status": "success",
            "message": "Oferta eliminada correctamente."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/jobs")
def list_my_jobs(
    limit: int = 10, 
    offset: int = 0, 
    search: str = None, 
    sort_by: str = "deadline_asc",
    current_user: dict = Depends(get_current_user)
):
    """Lista los trabajos que este reclutador ha publicado, incluyendo habilidades, requisitos y cantidad de postulantes."""
    try:
        db: Client = get_db()
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        recruiter_id = user_resp.data[0]["id"]
        
        query = db.table("JobPost").select("*", count="exact").eq("recruiter_id", recruiter_id)
        
        if search:
            query = query.ilike("title", f"%{search}%")
            
        if sort_by == "created_desc":
            query = query.order("created_at", desc=True)
        else:
            query = query.order("deadline")
            
        try:
            jobs_resp = query.range(offset, offset + limit - 1).execute()
            jobs = jobs_resp.data if jobs_resp.data else []
            total_count = jobs_resp.count if jobs_resp.count else 0
        except Exception as query_e:
            if "PGRST103" in str(query_e) or "Requested range not satisfiable" in str(query_e):
                return {"status": "success", "jobs": [], "has_more": False, "total_count": 0}
            raise query_e
        
        if not jobs:
            return {"status": "success", "jobs": [], "has_more": False, "total_count": total_count}
            
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
            j["requirements"] = job_skills_map.get(j["id"], [])
            j["applicants_count"] = app_counts.get(j["id"], 0)
            
        has_more = (offset + limit) < total_count
        
        return {
            "status": "success", 
            "jobs": jobs,
            "has_more": has_more,
            "total_count": total_count
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Error en list_my_jobs:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/candidates")
def get_job_candidates(job_id: int, current_user: dict = Depends(get_current_user)):
    """Matchmaking Básico: Obtiene los estudiantes de la base de datos para una oferta."""
    try:
        db: Client = get_db()
        
        # 1. Obtener requerimientos de la oferta
        reqs_resp = db.table("JobRequirement").select("skill_id").eq("job_id", job_id).execute()
        job_skills = set([r["skill_id"] for r in reqs_resp.data]) if reqs_resp.data else set()
        
        if job_skills:
            skills_resp = db.table("Skill").select("id, name").in_("id", list(job_skills)).execute()
            job_skills_dict = {s["id"]: s["name"] for s in skills_resp.data}
        else:
            job_skills_dict = {}

        # 2. Obtener estudiantes que aplicaron a esta oferta
        apps_resp = db.table("Application").select("student_id, status").eq("job_id", job_id).execute()
        
        applied_student_ids = []
        student_status_map = {}
        # Mapeo BD → UI (exacto, ya que BD tiene "En_revision", "Entrevista", etc.)
        status_to_ui = {
            "Pendiente": "revision",
            "En_revision": "revision",
            "Entrevista": "entrevista",
            "Rechazado": "rechazado",
            "Ganador": "ganador",
        }
        for a in apps_resp.data:
            applied_student_ids.append(a["student_id"])
            db_status = a.get("status") or "En_revision"
            ui_status = status_to_ui.get(db_status, "revision")
            student_status_map[a["student_id"]] = ui_status

        if not applied_student_ids:
            return {"status": "success", "candidates": [], "job_skills": list(job_skills_dict.values())}

        students_resp = db.table("Usuario").select("id, name, career, current_cycle, streak_count, email").in_("id", applied_student_ids).execute()
        students = students_resp.data

        # 3. Obtener las habilidades de estos estudiantes
        student_ids = [s["id"] for s in students]
        user_skills_resp = db.table("UserSkill").select("user_id, skill_id").in_("user_id", student_ids).execute()
        
        student_skills_map = {}
        for us in user_skills_resp.data:
            uid = us["user_id"]
            if uid not in student_skills_map:
                student_skills_map[uid] = set()
            student_skills_map[uid].add(us["skill_id"])

        all_skill_ids = list(set([us["skill_id"] for us in user_skills_resp.data]))
        all_skills_dict = {}
        if all_skill_ids:
            all_skills_resp = db.table("Skill").select("id, name").in_("id", all_skill_ids).execute()
            all_skills_dict = {s["id"]: s["name"] for s in all_skills_resp.data}

        # 4. Cargar modelo ML
        import os
        import joblib
        import random
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "random_forest_model.pkl")
        try:
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)
            ml_model = joblib.load(model_path)
        except Exception as e:
            print("Error cargando modelo ML:", e)
            ml_model = None

        results = []
        for student in students:
            s_skills = student_skills_map.get(student["id"], set())
            
            # Calcular skill match
            if job_skills:
                intersection = s_skills.intersection(job_skills)
                skill_match = (len(intersection) / len(job_skills)) * 100
                missing_skills = job_skills - intersection
                missing_names = [job_skills_dict.get(m, "Desconocido") for m in missing_skills]
            else:
                skill_match = 100
                missing_names = []

            # Extraer ciclo y racha del estudiante (necesarios para el cálculo de fit)
            cycle = student.get("current_cycle") or 1
            streak = student.get("streak_count") or 0

            # Fit score determinístico: basado en skill_match + bonus por ciclo y racha
            # (Cuando se integre Claude, esto se reemplazará con el análisis real de IA)
            cycle_bonus = min(cycle * 2, 20)       # máximo +20 por ciclo alto
            streak_bonus = min(streak * 0.5, 10)   # máximo +10 por racha
            ai_fit_score = min(int(skill_match * 0.7 + cycle_bonus + streak_bonus), 100)
            
            if not missing_names:
                pet_message = f"¡{student['name'].split()[0]} cumple con todos los requisitos técnicos! Excelente fit cultural."
            else:
                pet_message = f"¡Gran perfil! Solo le vendría bien reforzar: {', '.join(missing_names[:2])}."
            
            # 5. Predecir Probabilidad con ML
            prob = 0.5
            if ml_model:
                try:
                    prob = ml_model.predict_proba([[skill_match, ai_fit_score, cycle, streak]])[0][1]
                except Exception as e:
                    print("Error predecir:", e)

            knowledge = [all_skills_dict.get(sk, "Desconocido") for sk in s_skills]

            results.append({
                "id": student["id"],
                "name": student["name"],
                "career": student["career"] or "Estudiante UTP",
                "cycle": f"{cycle}vo ciclo",
                "email": student["email"],
                "cellphone": "999 999 999", 
                "match": int(skill_match),
                "ai_fit_score": ai_fit_score,
                "hiring_probability": int(prob * 100),
                "status": student_status_map.get(student["id"], "revision"),
                "softSkills": ["Trabajo en equipo"], # Placeholder para Frontend
                "knowledge": knowledge[:3],
                "pet_message": pet_message
            })

        # 6. Ordenar por probabilidad de contratación (Ranking)
        results = sorted(results, key=lambda x: x["hiring_probability"], reverse=True)
        
        for i, r in enumerate(results):
            r["ranking"] = i + 1

        return {
            "status": "success",
            "message": "Candidatos y predicciones obtenidas",
            "candidates": results,
            "job_skills": list(job_skills_dict.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class StatusUpdateRequest(BaseModel):
    status: str

@router.patch("/jobs/{job_id}/candidates/{student_id}/status")
def update_candidate_status(job_id: int, student_id: str, data: StatusUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Actualiza el estado de la postulación de un estudiante a una oferta."""
    try:
        db: Client = get_db()
        # Mapeo del frontend (minúsculas) → BD (valores exactos de la tabla)
        status_map = {
            "revision": "En_revision",
            "entrevista": "Entrevista",
            "rechazado": "Rechazado",
            "ganador": "Ganador",
        }
        db_status = status_map.get(data.status.lower(), "En_revision")
        print(f"[PATCH] job={job_id} student={student_id} status_in={data.status} -> db={db_status}")
            
        result = db.table("Application").update({"status": db_status}).eq("job_id", job_id).eq("student_id", student_id).execute()
        print(f"[PATCH] result={result.data}")
        return {"status": "success", "message": "Estado actualizado correctamente", "db_status": db_status}
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

from pydantic import BaseModel
class GenerateOfferRequest(BaseModel):
    prompt: str

@router.post("/generate_offer")
def generate_offer_ai(req: GenerateOfferRequest, current_user: dict = Depends(get_current_user)):
    """Genera una oferta estructurada a partir de un dictado de voz/texto y cobra 2 monedas."""
    try:
        db: Client = get_db()
        
        # 1. Validar reclutador y tokens
        user_resp = db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute()
        if not user_resp.data or user_resp.data[0].get("type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Solo reclutadores pueden usar esta función.")
        
        recruiter_id = user_resp.data[0]["id"]
        
        # Verificar y descontar tokens
        token_resp = db.table("CompanyTokenPool").select("total_tokens_available").eq("recruiter_id", recruiter_id).execute()
        
        if not token_resp.data or token_resp.data[0]["total_tokens_available"] < 2:
            raise HTTPException(status_code=400, detail="No tienes suficientes monedas. Se requieren 2 monedas.")
            
        current_tokens = token_resp.data[0]["total_tokens_available"]
        
        # Descontar tokens (Simulado/Real)
        db.table("CompanyTokenPool").update({"total_tokens_available": current_tokens - 2}).eq("recruiter_id", recruiter_id).execute()
        
        # 2. Obtener lista de skills actuales para pasarle a la IA
        skills_resp = db.table("Skill").select("id, name").execute()
        current_skills = [s["name"] for s in skills_resp.data] if skills_resp.data else []
        
        # 3. Llamar al servicio de IA
        from services.ia_service import generate_job_offer_with_ia
        offer_data = generate_job_offer_with_ia(req.prompt, current_skills)
        
        # 4. Mapear y crear skills devueltos por la IA
        skill_ids = []
        if "skills_required" in offer_data and isinstance(offer_data["skills_required"], list):
            # Obtener skills actualizados (por id)
            current_skills_map = {s["name"].lower(): s["id"] for s in skills_resp.data} if skills_resp.data else {}
            
            for skill_name in offer_data["skills_required"]:
                clean_name = str(skill_name).strip()
                if not clean_name: continue
                
                lower_name = clean_name.lower()
                if lower_name in current_skills_map:
                    skill_ids.append(current_skills_map[lower_name])
                else:
                    # Crear nueva skill
                    try:
                        new_skill_resp = db.table("Skill").insert({"name": clean_name}).execute()
                        if new_skill_resp.data:
                            new_id = new_skill_resp.data[0]["id"]
                            skill_ids.append(new_id)
                            current_skills_map[lower_name] = new_id
                    except Exception as e:
                        print("Error creating new skill:", e)
        
        # Reemplazar la lista de strings por la lista de IDs para el frontend
        offer_data["skills_required"] = skill_ids
        
        return {
            "status": "success",
            "message": "Oferta generada exitosamente. Se descontaron 2 monedas.",
            "data": offer_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Error en generate_offer_ai:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/generate_challenge")
def api_generate_challenge(job_id: int, current_user: dict = Depends(get_current_user)):
    """Llama a la IA para proponer un reto técnico basado en los requerimientos del job."""
    try:
        db: Client = get_db()
        
        # Validar permisos
        user_resp = db.table("Usuario").select("id, type").eq("email", current_user["email"]).execute()
        if not user_resp.data or user_resp.data[0].get("type") != "Recruiter":
            raise HTTPException(status_code=403, detail="Solo reclutadores.")
        recruiter_id = user_resp.data[0]["id"]
        
        # Obtener datos del Job
        job_resp = db.table("JobPost").select("title, description").eq("id", job_id).eq("recruiter_id", recruiter_id).execute()
        if not job_resp.data:
            raise HTTPException(status_code=404, detail="Oferta no encontrada o sin acceso.")
        
        job_data = job_resp.data[0]
        
        # Obtener habilidades requeridas
        reqs_resp = db.table("JobRequirement").select("skill_id").eq("job_id", job_id).execute()
        skill_ids = [r["skill_id"] for r in reqs_resp.data] if reqs_resp.data else []
        
        skills_names = []
        if skill_ids:
            skills_resp = db.table("Skill").select("name").in_("id", skill_ids).execute()
            skills_names = [s["name"] for s in skills_resp.data] if skills_resp.data else []
            
        # Generar con IA
        from services.ia_service import generate_technical_challenge
        ai_challenge = generate_technical_challenge(job_data["title"], job_data["description"], skills_names)
        
        return {
            "status": "success",
            "data": ai_challenge
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SponsorAiChallengeRequest(BaseModel):
    title: str
    description: str
    deliverables: str
    reward_coins: int
    reward_xp: int
    max_winners: int
    tokens_cost: int
    skill_id: Optional[int] = None

@router.post("/jobs/{job_id}/sponsor_ai_challenge")
def sponsor_ai_challenge(job_id: int, req: SponsorAiChallengeRequest, current_user: dict = Depends(get_current_user)):
    """Crea un nuevo Challenge y lo patrocina (SponsoredChallenge). Notifica a postulantes actuales."""
    try:
        db: Client = get_db()
        
        # 1. Validar reclutador y tokens
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        recruiter_id = user_resp.data[0]["id"]
        
        pool_resp = db.table("CompanyTokenPool").select("total_tokens_available").eq("recruiter_id", recruiter_id).execute()
        if not pool_resp.data:
            raise HTTPException(status_code=400, detail="No tienes cuenta de tokens.")
            
        current_tokens = pool_resp.data[0]["total_tokens_available"]
        if current_tokens < req.tokens_cost:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Necesitas {req.tokens_cost} monedas.")
            
        # 2. Descontar Tokens
        new_balance = current_tokens - req.tokens_cost
        db.table("CompanyTokenPool").update({"total_tokens_available": new_balance}).eq("recruiter_id", recruiter_id).execute()
        
        # 3. Obtener skill_id por defecto si no lo envían (tomamos el primero del job)
        skill_id = req.skill_id
        if not skill_id:
            reqs_resp = db.table("JobRequirement").select("skill_id").eq("job_id", job_id).execute()
            if reqs_resp.data:
                skill_id = reqs_resp.data[0]["skill_id"]
            else:
                # Fallback genérico, asumiendo que existe un skill ID 1
                skill_id = 1 
                
        # 4. Crear el Challenge
        challenge_data = {
            "skill_id": skill_id,
            "title": req.title,
            "description": f"{req.description}\n\nEntregables: {req.deliverables}",
            "reward_coins": req.reward_coins,
            "reward_xp": req.reward_xp,
            "challenge_type": "technical", # o puedes omitirlo si no está en tu esquema
            "author_id": recruiter_id
        }
        
        # Omitimos campos si no existen en BD, filtramos
        try:
            ch_resp = db.table("Challenge").insert(challenge_data).execute()
        except Exception:
            # Si falla por campos que no existen, intentamos el mínimo
            ch_resp = db.table("Challenge").insert({
                "skill_id": skill_id,
                "title": req.title,
                "reward_coins": req.reward_coins,
                "reward_xp": req.reward_xp
            }).execute()
            
        new_challenge_id = ch_resp.data[0]["id"]
        
        # 5. Crear el SponsoredChallenge
        sponsored_data = {
            "recruiter_id": recruiter_id,
            "challenge_id": new_challenge_id,
            "job_id": job_id,
            "max_winners": req.max_winners,
            "tokens_cost": req.tokens_cost,
            "min_career_score": 0
        }
        db.table("SponsoredChallenge").insert(sponsored_data).execute()
        
        return {
            "status": "success",
            "message": "Reto creado y patrocinado correctamente.",
            "new_balance": new_balance,
            "challenge_id": new_challenge_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Error sponsor AI:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/sponsored_challenges")
def get_sponsored_challenges(job_id: int, current_user: dict = Depends(get_current_user)):
    """Devuelve los retos que este reclutador ha patrocinado para esta oferta."""
    try:
        db: Client = get_db()
        
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        recruiter_id = user_resp.data[0]["id"]
        
        # Obtener los patrocinados
        sc_resp = db.table("SponsoredChallenge").select("id, challenge_id, max_winners, tokens_cost").eq("job_id", job_id).eq("recruiter_id", recruiter_id).execute()
        
        if not sc_resp.data:
            return {"status": "success", "challenges": []}
            
        challenge_ids = [sc["challenge_id"] for sc in sc_resp.data]
        ch_resp = db.table("Challenge").select("id, title, reward_coins").in_("id", challenge_ids).execute()
        
        challenges_map = {c["id"]: c for c in ch_resp.data}
        
        results = []
        for sc in sc_resp.data:
            c_info = challenges_map.get(sc["challenge_id"], {})
            results.append({
                "sponsored_id": sc["id"],
                "challenge_id": sc["challenge_id"],
                "title": c_info.get("title", "Reto desconocido"),
                "max_winners": sc["max_winners"],
                "tokens_cost": sc["tokens_cost"],
                "reward_coins": c_info.get("reward_coins", 0)
            })
            
        return {
            "status": "success",
            "challenges": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
