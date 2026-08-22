from fastapi import APIRouter, Depends
from app.security.auth import get_current_patient
from app.utils.response import success_response

router = APIRouter()

@router.get("/me")
async def get_me(patient: dict = Depends(get_current_patient)):
    return success_response(patient)
