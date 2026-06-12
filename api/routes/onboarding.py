from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models.schemas import OnboardingStudentRequest, OnboardingRecruiterRequest
from core.supabase_db import get_db
from supabase import Client
from services.email_service import send_verification_code
from api.dependencies.auth import get_current_user
import random
import string

router = APIRouter()

@router.get("/status")
def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """Devuelve el tipo/estado actual del usuario para saber si necesita onboarding."""
    try:
        db: Client = get_db()
        response = db.table("Usuario").select("*").eq("email", current_user["email"]).execute()
        
        if not response.data:
            # Auto-registrar usuario si no existe
            new_user = {
                "name": current_user.get("name") or "Usuario",
                "email": current_user["email"],
                "type": "Pending", 
                "status": "Active"
            }
            db.table("Usuario").insert(new_user).execute()
            return {"status": "success", "type": "Pending", "onboarding_complete": False, "user": new_user}
        
        user = response.data[0]
        user_type = user.get("type", "Pending")
        
        print(f"DEBUG /status - Email: {current_user['email']} - Type in DB: {user_type}")
        
        return {
            "status": "success",
            "type": user_type,
            "onboarding_complete": user_type in ["Student", "Company"],
            "user": user
        }
    except Exception as e:
        print(f"Error in get_onboarding_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/student")
def onboard_student(data: OnboardingStudentRequest, current_user: dict = Depends(get_current_user)):
    """Completa el onboarding de un estudiante."""
    try:
        db: Client = get_db()
        
        update_data = {
            "type": "Student",
            "career": data.career,
            "semester": data.semester,
            "goal": data.goal,
            "has_experience": data.has_experience,
            "experience_type": data.experience_type,
            "has_projects": data.has_projects,
            "target_company": data.target_company,
            "interest_area": data.interest_area,
            "status": "Active"
        }
        
        response = db.table("Usuario").update(update_data).eq("email", current_user["email"]).execute()
        
        if response.data:
            return {"status": "success", "message": "¡Onboarding completado! Bienvenido a CarrerOn.", "user": response.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    except HTTPException:
        raise
    except Exception as e:
        # Modo mock
        return {
            "status": "success",
            "message": "Onboarding completado (Modo Demo)",
            "user": {"email": data.email, "type": "Student", "career": data.career, "semester": data.semester}
        }

@router.post("/recruiter/request-code")
def recruiter_request_code(data: OnboardingRecruiterRequest):
    """Envía código de verificación al email corporativo del reclutador."""
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Enviar código al email corporativo
        send_verification_code(data.corporate_email, code)
        
        # Guardar datos temporales
        db: Client = get_db()
        db.table("Usuario").update({
            "company_name": data.company_name,
            "job_title": data.job_title,
            "corporate_email": data.corporate_email,
            "temp_code": code
        }).eq("email", data.email).execute()
        
        return {"status": "success", "message": f"Código enviado a {data.corporate_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class VerifyRecruiterRequest(BaseModel):
    email: str
    code: str

@router.post("/recruiter/verify")
def recruiter_verify_code(data: VerifyRecruiterRequest):
    """Verifica el código del reclutador y completa su onboarding."""
    try:
        db: Client = get_db()
        # Verificar el código usando la columna temp_code
        response = db.table("Usuario").select("temp_code").eq("email", data.email).execute()
        
        if response.data and response.data[0].get("temp_code") == data.code:
            # Código correcto, limpiar el código y cambiar el rol a Company
            db.table("Usuario").update({
                "type": "Company",
                "temp_code": None,
                "status": "Active"
            }).eq("email", data.email).execute()
            
            return {"status": "success", "message": "¡Verificación exitosa! Bienvenido como Reclutador."}
        else:
            raise HTTPException(status_code=400, detail="Código inválido o expirado.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
