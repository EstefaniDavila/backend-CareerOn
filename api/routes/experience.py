from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import ExperienceCreate
from api.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/")
def get_my_experiences(
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
            db.table("Experience")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "status": "success",
            "experiences": response.data
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def create_experience(
    data: ExperienceCreate,
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
            db.table("Experience")
            .insert({
                "user_id": user_id,
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

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{experience_id}")
def update_experience(
    experience_id: str,
    data: ExperienceCreate,
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
            db.table("Experience")
            .update({
                "company_name": data.company_name,
                "position": data.position,
                "employment_type": data.employment_type,
                "description": data.description,
                "start_date": str(data.start_date),
                "end_date": str(data.end_date) if data.end_date else None,
                "currently_working": data.currently_working
            })
            .eq("id", experience_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Experience no encontrada"
            )

        return {
            "status": "success",
            "message": "Experience actualizada correctamente",
            "experience": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{experience_id}")
def delete_experience(
    experience_id: str,
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
            db.table("Experience")
            .delete()
            .eq("id", experience_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Experience no encontrada"
            )

        return {
            "status": "success",
            "message": "Experience eliminada correctamente"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )