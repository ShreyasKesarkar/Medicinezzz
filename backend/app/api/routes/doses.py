from fastapi import APIRouter, Depends
from uuid import UUID
from typing import Optional
from app.database import db
from app.security.auth import get_current_patient
from app.services.dose_service import DoseService
from app.schemas.event import TakeDoseSchema, SkipDoseSchema, CorrectDoseSchema
from app.utils.response import success_response

router = APIRouter()

@router.post("/{id}/take")
async def take_dose(
    id: UUID,
    data: Optional[TakeDoseSchema] = None,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    remark = data.remark if data else None
    result = await DoseService.record_taken(conn, UUID(patient["patient_id"]), id, remark)
    return success_response(result, message="Dose recorded as taken")

@router.post("/{id}/skip")
async def skip_dose(
    id: UUID,
    data: Optional[SkipDoseSchema] = None,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    remark = data.remark if data else None
    result = await DoseService.record_skipped(conn, UUID(patient["patient_id"]), id, remark)
    return success_response(result, message="Dose recorded as skipped")

@router.post("/{id}/correct")
async def correct_dose(
    id: UUID,
    data: CorrectDoseSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    result = await DoseService.record_corrected(
        conn=conn,
        patient_id=UUID(patient["patient_id"]),
        dose_id=id,
        corrected_status=data.status,
        remark=data.remark
    )
    return success_response(result, message="Dose status corrected successfully")
