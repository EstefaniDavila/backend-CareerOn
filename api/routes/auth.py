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
        # Buscar usuario por email
        response = db.table("Usuario").select("*").eq("email", data.email).execute()
        
        if not response.data:
            # Crear nuevo usuario
            new_user = {
                "name": data.name,
                "email": data.email,
                "type": "Pending", 
                "status": "Active",
                "streak_count": 1,
                "coins_balance": 10 # Monedas de bienvenida
            }
            insert_resp = db.table("Usuario").insert(new_user).execute()
            user_data = insert_resp.data[0]
            message = "Usuario nuevo registrado. ¡Ganaste 10 monedas de bienvenida!"
        else:
            user_data = response.data[0]
            # Lógica básica de racha (streak) al iniciar sesión
            # En producción se debe comparar 'last_login' con la fecha actual
            new_streak = user_data.get("streak_count", 0) + 1
            new_coins = user_data.get("coins_balance", 0) + 5
            
            db.table("Usuario").update({
                "streak_count": new_streak,
                "coins_balance": new_coins
                # Aquí iría last_login: current_timestamp
            }).eq("id", user_data["id"]).execute()
            
            user_data["streak_count"] = new_streak
            user_data["coins_balance"] = new_coins
            
            message = f"¡Bienvenido de vuelta! Tu racha es de {new_streak} días. Ganaste 5 monedas."
            
        return {"status": "success", "message": message, "user": user_data}
    except Exception as e:
        return {
            "status": "warning", 
            "message": f"Login local (Modo Mock): {str(e)}",
            "user": {"name": data.name, "email": data.email, "type": "Pending"}
        }

@router.post("/send-code")
def send_code(data: EmailCodeRequest):
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        send_verification_code(data.email, code)
        db: Client = get_db()
        
        # Corregido: codigo_temp -> temp_code, correo -> email
        db.table("Usuario").update({"temp_code": code}).eq("email", data.email).execute()
        
        return {"status": "success", "message": "Código enviado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-code")
def verify_code(data: VerifyCodeRequest):
    try:
        db: Client = get_db()
        
        # Corregido: codigo_temp -> temp_code, correo -> email
        response = db.table("Usuario").select("temp_code").eq("email", data.email).execute()
        
        if response.data and response.data[0].get("temp_code") == data.code:
            # Corregido: tipo -> type, Empresa -> Recruiter
            db.table("Usuario").update({
                "type": "Recruiter",
                "temp_code": None
            }).eq("email", data.email).execute()
            
            # TODO: Crear el CompanyTokenPool con 5000 monedas gratis aquí
            
            return {"status": "success", "message": "Código validado. Ahora eres Reclutador."}
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
