from fastapi import APIRouter, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import ExperienceCreate

router = APIRouter()

@router.get("/")
def get_experiences():
    try:
        db: Client = get_db()

        response = (
            db.table("Experience")
            .select("*")
            .execute()
        )

        return {
            "status": "success",
            "experiences": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
def get_experiences_by_user(user_id: str):
    try:
        db: Client = get_db()

        response = (
            db.table("Experience")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "status": "success",
            "experiences": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_experience(data: ExperienceCreate):
    try:
        db: Client = get_db()

        response = (
            db.table("Experience")
            .insert({
                "user_id": str(data.user_id),
                "company_name": data.company_name,
                "position": data.position,
                "employment_type": data.employment_type,
                "description": data.description,
                "start_date": str(data.start_date),
                "end_date": str(data.end_date) if data.end_date else None,
                "currently_working": data.currently_working
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "Experience creada correctamente",
            "experience": response.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{experience_id}")
def update_experience(experience_id: str, data: ExperienceCreate):
    try:
        db: Client = get_db()

        payload = data.dict(exclude_unset=True)
        payload.pop("id", None)  # por seguridad

        response = (
            db.table("Experience")
            .update(payload)
            .eq("id", experience_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "Experience actualizada",
            "experience": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experience_id}")
def delete_experience(experience_id: str):
    try:
        db: Client = get_db()

        db.table("Experience") \
            .delete() \
            .eq("id", experience_id) \
            .execute()

        return {
            "status": "success",
            "message": "Experience eliminada correctamente"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))