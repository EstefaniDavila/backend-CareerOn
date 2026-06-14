from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import Client
from core.supabase_db import get_db
from api.dependencies.auth import get_current_user
from services.ia_service import process_interview_message, evaluate_interview

router = APIRouter()

class StartInterviewRequest(BaseModel):
    mode: str  # "practice" o "job_specific"
    job_id: Optional[int] = None
    theme: Optional[str] = None

class Message(BaseModel):
    role: str # "user" o "model"
    content: str
    images: Optional[List[str]] = None # Base64 images for multimodal

class InterviewMessageRequest(BaseModel):
    history: List[Message]
    job_context: Optional[str] = None

class FinishInterviewRequest(BaseModel):
    history: List[Message]
    job_context: Optional[str] = None

@router.post("/start")
def start_interview(data: StartInterviewRequest, current_user: dict = Depends(get_current_user)):
    """Inicia una entrevista, obteniendo contexto si es job_specific, o restando 100 monedas si es práctica."""
    db: Client = get_db()
    job_context = None
    
    if data.mode == "practice":
        # Check and deduct 100 coins
        user_resp = db.table("Usuario").select("id, coins_balance").eq("email", current_user["email"]).execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        user = user_resp.data[0]
        if user["coins_balance"] < 100:
            raise HTTPException(status_code=400, detail="No tienes suficientes monedas. Necesitas 100 monedas para simular.")
            
        new_balance = user["coins_balance"] - 100
        db.table("Usuario").update({"coins_balance": new_balance}).eq("id", user["id"]).execute()
        
        # Set custom theme
        theme_text = data.theme if data.theme else "Desarrollo de Software General"
        job_context = f"Práctica General. Tema elegido por el usuario: {theme_text}. MÁXIMO 2 PREGUNTAS."
        
    elif data.mode == "job_specific" and data.job_id:
        # Obtener datos de la oferta
        try:
            job_resp = db.table("JobPost").select("title, description, job_type").eq("id", data.job_id).execute()
            if job_resp.data:
                job = job_resp.data[0]
                job_context = f"Posición: {job.get('title', 'N/A')}. Tipo: {job.get('job_type', 'N/A')}. Descripción: {job.get('description', 'N/A')}"
        except Exception as e:
            print("Error obteniendo contexto del empleo:", e)
            
    # Primera pregunta de la IA
    first_question = process_interview_message(history=[], job_context=job_context)
    
    return {
        "status": "success",
        "job_context": job_context,
        "first_question": first_question
    }

@router.post("/message")
def send_message(data: InterviewMessageRequest, current_user: dict = Depends(get_current_user)):
    """Recibe el historial y fotos del usuario, y devuelve la respuesta de la IA."""
    history_dicts = [msg.dict() for msg in data.history]
    reply = process_interview_message(history=history_dicts, job_context=data.job_context)
    return {
        "status": "success",
        "reply": reply
    }

@router.post("/finish")
def finish_interview(data: FinishInterviewRequest, current_user: dict = Depends(get_current_user)):
    """Evalúa la entrevista y suma monedas y experiencia."""
    db: Client = get_db()
    
    # Evaluar con IA
    history_dicts = [msg.dict() for msg in data.history]
    evaluation = evaluate_interview(history=history_dicts, job_context=data.job_context)
    score = evaluation.get("score", 0)
    
    # Calcular recompensas
    coins_reward = 0
    xp_reward = 0
    if score >= 80:
        coins_reward = 10
        xp_reward = 100
    elif score >= 70:
        coins_reward = 5
        xp_reward = 75
    elif score >= 60:
        coins_reward = 3
        xp_reward = 50
        
    # Obtener usuario para recompensas y guardar historial
    user_resp = db.table("Usuario").select("id, coins_balance").eq("email", current_user["email"]).execute()
    if user_resp.data:
        user = user_resp.data[0]
        
        # Otorgar recompensas en DB
        if coins_reward > 0 or xp_reward > 0:
            new_coins = user.get("coins_balance", 0) + coins_reward
            db.table("Usuario").update({"coins_balance": new_coins}).eq("id", user["id"]).execute()
            
            # Obtener mascota (Pet) para dar XP
            pet_resp = db.table("Pet").select("id, experience_points").eq("user_id", user["id"]).execute()
            if pet_resp.data:
                pet = pet_resp.data[0]
                new_xp = pet.get("experience_points", 0) + xp_reward
                db.table("Pet").update({"experience_points": new_xp}).eq("id", pet["id"]).execute()
        
        # Obtener job_id del contexto si existe
        job_id = None
        if data.job_context and data.job_context.startswith("Job ID: "):
            try:
                job_id = int(data.job_context.split(":")[1].strip())
            except Exception:
                pass

        # Guardar historial de la entrevista SIEMPRE
        try:
            insert_data = {
                "user_id": user["id"],
                "score": score,
                "feedback": evaluation.get("feedback", ""),
                "transcript": history_dicts
            }
            if job_id:
                insert_data["job_id"] = job_id
            db.table("mock_interviews").insert(insert_data).execute()
        except Exception as e:
            print("Error guardando el historial de la entrevista:", e)

    return {
        "status": "success",
        "evaluation": evaluation,
        "rewards": {
            "coins": coins_reward,
            "xp": xp_reward
        }
    }
