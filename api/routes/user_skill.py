from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import UserSkillCreate
from api.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/")
def get_my_skills(
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data[0]["id"]

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

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def create_user_skill(
    data: UserSkillCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data[0]["id"]

        response = (
            db.table("UserSkill")
            .insert({
                "user_id": user_id,
                "skill_id": data.skill_id,
                "level": data.level
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "Skill agregada correctamente",
            "user_skill": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{skill_id}")
def update_user_skill(
    skill_id: int,
    data: UserSkillCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data[0]["id"]

        response = (
            db.table("UserSkill")
            .update({
                "level": data.level
            })
            .eq("user_id", user_id)
            .eq("skill_id", skill_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="UserSkill no encontrada"
            )

        return {
            "status": "success",
            "message": "Nivel actualizado correctamente",
            "user_skill": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{skill_id}")
def delete_user_skill(
    skill_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data[0]["id"]

        response = (
            db.table("UserSkill")
            .delete()
            .eq("user_id", user_id)
            .eq("skill_id", skill_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="UserSkill no encontrada"
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