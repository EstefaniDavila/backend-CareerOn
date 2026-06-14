from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from core.supabase_db import get_db
from models.schemas import EducationCreate
from api.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/")
def get_educations(
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .single()
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data["id"]

        response = (
            db.table("Education")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "status": "success",
            "educations": response.data
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/")
def create_education(
    data: EducationCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .single()
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data["id"]

        response = (
            db.table("Education")
            .insert({
                "user_id": user_id,
                "institution": data.institution,
                "degree": data.degree,
                "field_of_study": data.field_of_study,
                "start_date": str(data.start_date),
                "end_date": str(data.end_date) if data.end_date else None,
                "currently_studying": data.currently_studying
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "Educación creada correctamente",
            "education": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{education_id}")
def update_education(
    education_id: str,
    data: EducationCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .single()
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data["id"]

        check = (
            db.table("Education")
            .select("id")
            .eq("id", education_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not check.data:
            raise HTTPException(
                status_code=403,
                detail="No autorizado"
            )

        response = (
            db.table("Education")
            .update({
                "institution": data.institution,
                "degree": data.degree,
                "field_of_study": data.field_of_study,
                "start_date": str(data.start_date),
                "end_date": str(data.end_date) if data.end_date else None,
                "currently_studying": data.currently_studying
            })
            .eq("id", education_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "Educación actualizada correctamente",
            "education": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{education_id}")
def delete_education(
    education_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        db: Client = get_db()

        user_resp = (
            db.table("Usuario")
            .select("id")
            .eq("email", current_user["email"])
            .single()
            .execute()
        )

        if not user_resp.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        user_id = user_resp.data["id"]

        check = (
            db.table("Education")
            .select("id")
            .eq("id", education_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not check.data:
            raise HTTPException(
                status_code=403,
                detail="No autorizado"
            )

        db.table("Education") \
            .delete() \
            .eq("id", education_id) \
            .eq("user_id", user_id) \
            .execute()

        return {
            "status": "success",
            "message": "Educación eliminada correctamente"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )