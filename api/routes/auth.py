from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models.schemas import LoginRequest
from core.supabase_db import get_db
from supabase import Client
from services.email_service import send_verification_code
import random
import string

router = APIRouter()

class EmailCodeRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

@router.post("/login")
def login_with_microsoft(data: LoginRequest):
    try:
        db: Client = get_db()
        response = db.table("Usuario").select("*").eq("email", data.email).execute()
        
        if not response.data:
            new_user = {
                "name": data.name,
                "email": data.email,
                "type": "Pending", 
                "status": "Active"
            }
            insert_resp = db.table("Usuario").insert(new_user).execute()
            user_data = insert_resp.data[0]
            message = "Usuario nuevo registrado como Pendiente"
        else:
            user_data = response.data[0]
            message = "Usuario autenticado exitosamente"
            
        return {"status": "success", "message": message, "user": user_data}
    except Exception as e:
        return {
            "status": "warning", 
            "message": "Login exitoso (Modo Mock - Supabase no configurado)",
            "user": {"name": data.name, "email": data.email, "type": "Pending"}
        }

@router.post("/send-code")
def send_code(data: EmailCodeRequest):
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        send_verification_code(data.email, code)
        db: Client = get_db()
        db.table("Usuario").update({"codigo_temp": code}).eq("correo", data.email).execute()
        
        return {"status": "success", "message": "Código enviado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-code")
def verify_code(data: VerifyCodeRequest):
    try:
        db: Client = get_db()
        response = db.table("Usuario").select("codigo_temp").eq("correo", data.email).execute()
        
        if response.data and response.data[0].get("codigo_temp") == data.code:
            db.table("Usuario").update({
                "tipo": "Empresa",
                "codigo_temp": None
            }).eq("correo", data.email).execute()
            
            return {"status": "success", "message": "Código validado. Ahora eres Empresa."}
        else:
            raise HTTPException(status_code=400, detail="Código inválido o expirado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from api.dependencies.auth import get_current_user

@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Ruta Protegida de ejemplo. 
    Solo puedes acceder si Axios te envió con un token válido de Microsoft.
    """
    return {
        "status": "success",
        "message": "¡Tienes acceso a esta ruta protegida!",
        "user_from_token": current_user
    }
