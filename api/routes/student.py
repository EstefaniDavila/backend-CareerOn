from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import shutil
from core.supabase_db import get_db
from supabase import Client
from typing import Dict, Any
from api.dependencies.auth import get_current_user
from services.ia_service import generate_quest_challenge, evaluate_quest_answer

router = APIRouter()

DEMO_EMAIL = "estefanidaviladev@gmail.com"

@router.get("/profile")
def get_student_profile(current_user: dict = Depends(get_current_user)):
    try:
        db: Client = get_db()
        user_resp = db.table("Usuario").select("*").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            print(f"Usuario {current_user['email']} no encontrado. Usando DEMO_EMAIL: {DEMO_EMAIL}")
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
        
        app_resp = db.table("Application").select("id, status").eq("student_id", user_id).execute()
        applications_count = len(app_resp.data) if app_resp.data else 0
        
        interviews_count = sum(1 for app in (app_resp.data or []) if app.get("status") == "Entrevista")

        jobs_resp = db.table("JobPost").select("id", count="exact").eq("status", "publicada").execute()
        active_offers_count = jobs_resp.count if jobs_resp.count is not None else 0

        coins = user_data.get("coins_balance", 0)

        return {
            "status": "success",
            "data": {
                "user": user_data,
                "experiences": experiences,
                "projects": projects,
                "skills": skills,
                "languages": languages,
                "current_cv": current_cv,
                "applications_count": applications_count,
                "interviews_count": interviews_count,
                "active_offers_count": active_offers_count,
                "coins": coins
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        db: Client = get_db()
        
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
            
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_id = user_resp.data[0]["id"]
        
        filename = file.filename
        if filename.startswith(f"{user_id}_"):
            file_location = f"uploads/{filename}"
        else:
            file_location = f"uploads/{user_id}_{filename}"
        
        import os
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        if filename.startswith(f"{user_id}_"):
            file_url = f"http://localhost:8000/uploads/{filename}"
        else:
            file_url = f"http://localhost:8000/uploads/{user_id}_{filename}"
        
        db.table("Resume").update({"is_default": False}).eq("user_id", user_id).execute()
        
        new_resume = {
            "user_id": user_id,
            "title": f"CV Generado - {filename}",
            "file_url": file_url,
            "is_default": True
        }
        inserted = db.table("Resume").insert(new_resume).execute()
        db.table("Usuario").update({"portfolio_url": file_url}).eq("id", user_id).execute()
        
        try:
            from pypdf import PdfReader
            from services.ia_service import optimize_cv_with_gemini
            
            reader = PdfReader(file_location)
            cv_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text: cv_text += text + "\n"
            
            if cv_text.strip():
                ia_result = optimize_cv_with_gemini(cv_text)
                datos = ia_result.get("datos_extraidos", {})
                
                for hab in datos.get("habilidades", []):
                    sk_resp = db.table("Skill").select("id").eq("name", hab).execute()
                    if sk_resp.data:
                        sk_id = sk_resp.data[0]["id"]
                    else:
                        new_sk = db.table("Skill").insert({"name": hab, "category": "Otra"}).execute()
                        sk_id = new_sk.data[0]["id"]
                        
                    usr_sk_resp = db.table("UserSkill").select("*").eq("user_id", user_id).eq("skill_id", sk_id).execute()
                    if not usr_sk_resp.data:
                        db.table("UserSkill").insert({"user_id": user_id, "skill_id": sk_id, "level": "Intermedio"}).execute()

                for idioma in datos.get("idiomas", []):
                    lang_resp = db.table("Language").select("id").eq("name", idioma).execute()
                    if lang_resp.data:
                        lang_id = lang_resp.data[0]["id"]
                    else:
                        new_lang = db.table("Language").insert({"name": idioma}).execute()
                        lang_id = new_lang.data[0]["id"]
                        
                    usr_lang_resp = db.table("UserLanguage").select("*").eq("user_id", user_id).eq("language_id", lang_id).execute()
                    if not usr_lang_resp.data:
                        db.table("UserLanguage").insert({"user_id": user_id, "language_id": lang_id, "level": "Avanzado"}).execute()

                # Insertar Experiencia
                for exp in datos.get("experiencia", []):
                    # Chequeo simple por titulo de cargo para no duplicar
                    ex_resp = db.table("Experience").select("*").eq("user_id", user_id).eq("position", exp.get("cargo", "Cargo")).execute()
                    if not ex_resp.data:
                        db.table("Experience").insert({
                            "user_id": user_id,
                            "company_name": exp.get("empresa", "Empresa Desconocida"),
                            "position": exp.get("cargo", "Cargo"),
                            "employment_type": "Full-time",
                            "start_date": "2020-01-01",  # Dummy, la IA manda string de fechas, requiere parseo complejo, ponemos dummy
                            "description": exp.get("descripcion", "")
                        }).execute()

                for proj in datos.get("proyectos", []):
                    pr_resp = db.table("Project").select("*").eq("user_id", user_id).eq("title", proj.get("titulo", "Proyecto")).execute()
                    if not pr_resp.data:
                        db.table("Project").insert({
                            "user_id": user_id,
                            "title": proj.get("titulo", "Proyecto"),
                            "description": proj.get("descripcion", "")
                        }).execute()
                        
        except Exception as inner_e:
            print(f"Error procesando CV con IA: {inner_e}")
            
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
            user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
            
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
def add_skill(data: SkillData, current_user: dict = Depends(get_current_user)):
    db: Client = get_db()
    user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
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

@router.get("/quests/generate")
def get_quest_challenge(skill: str, current_user: dict = Depends(get_current_user)):
    """Genera una pregunta técnica (texto libre o múltiple) usando IA."""
    return generate_quest_challenge(skill)

class QuestEvalData(BaseModel):
    skill: str
    question: str
    answer: str

@router.post("/quests/evaluate")
def evaluate_quest(data: QuestEvalData, current_user: dict = Depends(get_current_user)):
    """Evalúa la respuesta del usuario con IA."""
    return evaluate_quest_answer(data.skill, data.question, data.answer)

@router.get("/jobs")
def get_all_jobs(current_user: dict = Depends(get_current_user)):
    """Obtiene ofertas de trabajo ordenadas por recomendación para el estudiante."""
    db: Client = get_db()
    try:
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            return []
        user_id = user_resp.data[0]["id"]
        
        student_skills_resp = db.table("UserSkill").select("Skill(name)").eq("user_id", user_id).execute()
        student_skills = [s["Skill"]["name"].lower() for s in student_skills_resp.data if s.get("Skill")] if student_skills_resp.data else []
        student_skills_set = set(student_skills)

        jobs_resp = db.table("JobPost").select("*").eq("status", "publicada").execute()
        jobs = jobs_resp.data
        users_resp = db.table("Usuario").select("id, company_name").eq("type", "Recruiter").execute()
        recruiters = {u["id"]: u.get("company_name", "Empresa Confidencial") for u in users_resp.data}
        
        skills_resp = db.table("Skill").select("id, name").execute()
        skills_dict = {s["id"]: s["name"] for s in skills_resp.data}
        
        reqs_resp = db.table("JobRequirement").select("job_id, skill_id").execute()
        job_skills_map = {}
        for req in reqs_resp.data:
            job_id = req["job_id"]
            skill_name = skills_dict.get(req["skill_id"])
            if skill_name:
                if job_id not in job_skills_map:
                    job_skills_map[job_id] = []
                job_skills_map[job_id].append(skill_name)
                
        apps_resp = db.table("Application").select("job_id").execute()
        app_counts = {}
        for app in apps_resp.data:
            jid = app["job_id"]
            app_counts[jid] = app_counts.get(jid, 0) + 1
        
        formatted_jobs = []
        from datetime import datetime, timezone
        
        for j in jobs:
            posted_days_ago = 0
            if j.get("created_at"):
                try:
                    created_date = datetime.fromisoformat(j["created_at"].replace("Z", "+00:00"))
                    posted_days_ago = (datetime.now(timezone.utc) - created_date).days
                except:
                    pass
            
            req_skills = job_skills_map.get(j["id"], [])
            req_skills_lower = [s.lower() for s in req_skills]
            if req_skills_lower:
                matched = student_skills_set.intersection(set(req_skills_lower))
                match_score = int((len(matched) / len(req_skills_lower)) * 100)
            else:
                match_score = 100 

            formatted_jobs.append({
                "id": j["id"],
                "title": j["title"],
                "company": recruiters.get(j["recruiter_id"], "Empresa Confidencial"),
                "location": j.get("location") or "Remoto", 
                "type": j.get("job_type") or "Tiempo completo",
                "description": j["description"],
                "skills_required": req_skills if req_skills else ["React", "CSS"],
                "posted_days_ago": max(posted_days_ago, 0),
                "applicants_count": app_counts.get(j["id"], 0),
                "is_match": match_score >= 50, # Solo true si es buen match
                "match_score": match_score,
                "salary_range": j.get("salary_range") or "No especificado",
            })
        formatted_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return {
            "jobs": formatted_jobs,
            "empty_profile": len(student_skills_set) == 0
        }
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


@router.get("/applications/{status}")
def get_my_applications_by_status(
    status: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()

        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_id = user_resp.data[0]["id"]

        query = db.table("Application") \
            .select("""
                *,
                JobPost (
                    id,
                    title,
                    description,
                    location,
                    salary_range
                )
            """) \
            .eq("student_id", user_id)
            
        if status == "Entrevista":
            query = query.in_("status", ["Entrevista", "Reto Técnico"])
        else:
            query = query.eq("status", status)
            
        apps_resp = query.execute()

        return apps_resp.data

    except HTTPException:
        raise
    except Exception as e:
        print("Error en get_my_applications_by_status:", e)
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class SubmitChallengeRequest(BaseModel):
    url: str | None = None

@router.post("/applications/{application_id}/submit-challenge")
def submit_challenge(application_id: int, req: SubmitChallengeRequest, current_user: dict = Depends(get_current_user)):
    try:
        db: Client = get_db()
        db.table("Application").update({"status": "Entrevista"}).eq("id", application_id).execute()
        
        if req.url:
            db.table("Usuario").update({"github_url": req.url}).eq("email", current_user["email"]).execute()
            
        return {"status": "success"}
    except Exception as e:
        print("Error submitting challenge:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (db.table("Usuario").select("id").eq("email", current_user["email"]).execute())

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data[0]["id"]

        application_resp = (
            db.table("Application")
            .select("id")
            .eq("id", application_id)
            .eq("student_id", user_id)
            .execute()
        )

        if not application_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Postulación no encontrada"
            )

        (
            db.table("Application")
            .delete()
            .eq("id", application_id)
            .eq("student_id", user_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "Postulación eliminada correctamente"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/company-challenges")
def get_company_challenges(current_user: dict = Depends(get_current_user)):
    """Obtiene los retos patrocinados de los empleos a los que el estudiante postuló y pasó el filtro."""
    try:
        db: Client = get_db()

        # 1. Obtener ID del estudiante
        user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            user_resp = db.table("Usuario").select("id").eq("email", DEMO_EMAIL).execute()
        
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_id = user_resp.data[0]["id"]

        # 2. Buscar aplicaciones en "Reto Técnico"
        apps_resp = db.table("Application").select("id, job_id, JobPost(title, recruiter_id)").eq("student_id", user_id).eq("status", "Reto Técnico").execute()
        if not apps_resp.data:
            return []

        job_ids = [app["job_id"] for app in apps_resp.data]
        
        # Guardar nombres de reclutadores/empresas
        recruiter_ids = list(set([app["JobPost"]["recruiter_id"] for app in apps_resp.data if app.get("JobPost")]))
        companies_map = {}
        if recruiter_ids:
            rec_resp = db.table("Usuario").select("id, company_name").in_("id", recruiter_ids).execute()
            companies_map = {r["id"]: r.get("company_name", "Empresa Confidencial") for r in rec_resp.data}

        # 3. Buscar SponsoredChallenges
        sc_resp = db.table("SponsoredChallenge").select("*").in_("job_id", job_ids).execute()
        if not sc_resp.data:
            return []

        challenge_ids = [sc["challenge_id"] for sc in sc_resp.data]

        # 4. Buscar retos
        ch_resp = db.table("Challenge").select("*").in_("id", challenge_ids).execute()
        challenges_map = {c["id"]: c for c in ch_resp.data}

        results = []
        for app in apps_resp.data:
            app_job_id = app["job_id"]
            sc = next((x for x in sc_resp.data if x["job_id"] == app_job_id), None)
            if not sc:
                continue
            ch = challenges_map.get(sc["challenge_id"])
            if not ch:
                continue
            
            job_title = app.get("JobPost", {}).get("title", "Empleo")
            recruiter_id = app.get("JobPost", {}).get("recruiter_id")
            company_name = companies_map.get(recruiter_id, "Empresa Confidencial")
            
            results.append({
                "application_id": app["id"],
                "job_id": app_job_id,
                "job_title": job_title,
                "company_name": company_name,
                "challenge": ch,
                "sponsored_challenge": sc
            })

        return results

    except HTTPException:
        raise
    except Exception as e:
        print("Error en get_company_challenges:", e)
        raise HTTPException(status_code=500, detail=str(e))
