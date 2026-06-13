from fastapi import APIRouter, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import UserSkillCreate

router = APIRouter()

@router.get("/")
def get_user_skills():
    try:
        db: Client = get_db()

        response = (
            db.table("UserSkill")
            .select("*")
            .execute()
        )

        return {
            "status": "success",
            "user_skills": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    


@router.get("/user/{user_id}")
def get_user_skills_by_user(user_id: str):
    try:
        db: Client = get_db()

        response = (
            db.table("UserSkill")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "status": "success",
            "user_skills": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def create_user_skill(data: UserSkillCreate):
    try:
        db: Client = get_db()

        response = (
            db.table("UserSkill")
            .insert({
                "user_id": str(data.user_id),
                "skill_id": data.skill_id,
                "level": data.level
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "UserSkill creada correctamente",
            "user_skill": response.data[0]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{user_id}/{skill_id}")
def update_user_skill(
    user_id: str,
    skill_id: int,
    level: str
):
    try:
        db: Client = get_db()

        response = (
            db.table("UserSkill")
            .update({
                "level": level
            })
            .eq("user_id", user_id)
            .eq("skill_id", skill_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "Nivel actualizado",
            "user_skill": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{user_id}/{skill_id}")
def delete_user_skill(
    user_id: str,
    skill_id: int
):
    try:
        db: Client = get_db()

        response = (
            db.table("UserSkill")
            .delete()
            .eq("user_id", user_id)
            .eq("skill_id", skill_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "UserSkill eliminada correctamente"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
