from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from core.supabase_db import get_db
from api.dependencies.auth import get_current_user
from services.ia_service import analyze_gap_with_gemini, optimize_cv_with_gemini
from pydantic import BaseModel
import io
import uuid
from fastapi import UploadFile, File

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

@router.post("/optimize-cv-upload")
async def optimize_cv_upload(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Recibe un PDF, extrae el texto, lo guarda en Supabase Storage y lo analiza con Gemini.
    """
    try:
        from pypdf import PdfReader
        
        content = await file.read()
        
        # 1. Extraer texto del PDF
        try:
            reader = PdfReader(io.BytesIO(content))
            cv_text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    cv_text += extracted + "\n"
        except Exception as pdf_err:
            raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo PDF: {str(pdf_err)}")
            
        if len(cv_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="El PDF parece estar vacío o ser una imagen sin texto (necesita ser texto seleccionable).")

        # 2. Subir a Supabase Storage
        db: Client = get_db()
        file_ext = file.filename.split(".")[-1]
        safe_email = current_user['email'].split('@')[0]
        unique_filename = f"{safe_email}_{uuid.uuid4().hex[:8]}.{file_ext}"
        
        file_url = None
        try:
            # Sube al bucket 'cv_students' (debe existir y ser público en Supabase)
            db.storage.from_("cv_students").upload(unique_filename, content, {"content-type": file.content_type})
            file_url = db.storage.from_("cv_students").get_public_url(unique_filename)
        except Exception as e:
            print(f"Advertencia: No se pudo subir el archivo a Supabase Storage. ¿Existe el bucket 'cv_students'? Error: {e}")
            
        # 3. Guardar la URL en la base de datos (opcional si la tabla existe)
        if file_url:
            user_resp = db.table("Usuario").select("id").eq("email", current_user["email"]).execute()
            if user_resp.data:
                user_id = user_resp.data[0]["id"]
                try:
                    db.table("Resume").insert({
                        "user_id": user_id,
                        "title": file.filename,
                        "file_url": file_url,
                        "is_default": True
                    }).execute()
                except Exception as db_e:
                    print(f"Advertencia: No se pudo guardar el registro en la tabla Resume: {db_e}")

        # 4. Enviar a Gemini para optimizar
        analysis = optimize_cv_with_gemini(cv_text)
        
        return {
            "status": "success",
            "message": "CV procesado y guardado correctamente.",
            "file_url": file_url,
            "data": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
