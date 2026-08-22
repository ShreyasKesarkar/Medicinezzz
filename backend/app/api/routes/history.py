from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional
from app.database import db
from app.security.auth import get_current_patient
from app.repositories.history_repository import HistoryRepository
from app.utils.response import success_response

router = APIRouter()

@router.get("")
async def get_history(
    medicine_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    medicine_type_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    logs = await HistoryRepository.get_history(
        conn=conn,
        patient_id=UUID(patient["patient_id"]),
        medicine_id=medicine_id,
        event_type=event_type,
        medicine_type_id=medicine_type_id,
        limit=limit,
        offset=offset
    )
    return success_response(logs)

@router.get("/medicines/{medicine_id}")
async def get_medicine_history(
    medicine_id: UUID,
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    logs = await HistoryRepository.get_history(
        conn=conn,
        patient_id=UUID(patient["patient_id"]),
        medicine_id=medicine_id,
        event_type=event_type,
        limit=limit,
        offset=offset
    )
    return success_response(logs)
