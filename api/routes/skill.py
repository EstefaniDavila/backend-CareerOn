from fastapi import APIRouter, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import SkillCreate

router = APIRouter()

@router.get("/")
def get_skills():
    try:
        db: Client = get_db()

        response = (
            db.table("Skill")
            .select("*")
            .execute()
        )

        return {
            "status": "success",
            "skills": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def create_skill(data: SkillCreate):
    try:
        db: Client = get_db()

        response = (
            db.table("Skill")
            .insert({
                "name": data.name,
                "category": data.category
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "Skill creada correctamente",
            "skill": response.data[0]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{skill_id}")
def update_skill(skill_id: int, data: SkillCreate):
    try:
        db: Client = get_db()

        response = (
            db.table("Skill")
            .update({
                "name": data.name,
                "category": data.category
            })
            .eq("id", skill_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Skill no encontrada"
            )

        return {
            "status": "success",
            "message": "Skill actualizada correctamente",
            "skill": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{skill_id}")
def delete_skill(skill_id: int):
    try:
        db: Client = get_db()

        response = (
            db.table("Skill")
            .delete()
            .eq("id", skill_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Skill no encontrada"
            )

        return {
            "status": "success",
            "message": "Skill eliminada correctamente"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )