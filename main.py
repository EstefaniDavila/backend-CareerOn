from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth
from api.routes import onboarding
from api.routes import recruiter
from api.routes import ai_coach
from api.routes import skill
from api.routes import user_skill
from api.routes import experience
from api.routes import student

app = FastAPI(
    title="CarrerOn API",
    description="Backend para el copiloto de empleabilidad de UTP",
    version="1.0.0"
)

import os
from fastapi.staticfiles import StaticFiles

# Habilitar CORS para permitir que React (5173) y React Native se conecten
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],  # Permitir local y emuladores
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir los routers (rutas divididas por módulos)
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(recruiter.router, prefix="/api/recruiter", tags=["Reclutador"])
app.include_router(ai_coach.router, prefix="/api/ai", tags=["Coach IA"])
app.include_router(skill.router, prefix="/api/skill", tags=["Habilidades"])
app.include_router(user_skill.router, prefix="/api/user-skill", tags=["Habilidades de Usuario"])
app.include_router(experience.router, prefix="/api/experience", tags=["Experiencia"])
app.include_router(student.router, prefix="/api/student", tags=["Estudiante"])
@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la API Profesional de CarrerOn!"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "El backend está funcionando correctamente."}
