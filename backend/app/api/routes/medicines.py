from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID
from datetime import date, timedelta, datetime
from typing import Optional
from app.database import db
from app.security.auth import get_current_patient
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.instruction_repository import InstructionRepository
from app.repositories.history_repository import HistoryRepository
from app.services.medicine_service import MedicineService
from app.services.scheduler_service import SchedulerService
from app.schemas.medicine import MedicineCreateSchema, MedicineEditSchema, PauseMedicineSchema
from app.utils.response import success_response

router = APIRouter()

async def trigger_event_generation(conn, patient_id: str):
    # Generates events for a rolling 37-day window (7 days in past, 30 days in future)
    today_local = date.today()
    start_gen = today_local - timedelta(days=7)
    end_gen = today_local + timedelta(days=30)
    await SchedulerService.generate_events_for_patient(conn, UUID(patient_id), start_gen, end_gen)

@router.get("")
async def list_medicines(
    status: Optional[str] = None,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicines = await MedicineRepository.get_medicines(conn, UUID(patient["patient_id"]), status)
    return success_response(medicines)

@router.get("/types")
async def list_types(
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    types = await MedicineRepository.get_medicine_types(conn, UUID(patient["patient_id"]))
    return success_response(types)

@router.get("/units")
async def list_units(
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    units = await MedicineRepository.get_dosage_units(conn, UUID(patient["patient_id"]))
    return success_response(units)

@router.post("")
async def create_medicine(
    data: MedicineCreateSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    m_id = await MedicineService.create_medicine(conn, UUID(patient["patient_id"]), data)
    # Automatically generate events for this patient
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response({"id": str(m_id)}, message="Medicine created successfully")

@router.get("/{id}")
async def get_medicine(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
        
    # Get active schedules
    schedules = await ScheduleRepository.get_schedules_by_medicine_id(conn, id)
    # Get active instructions
    instructions = await InstructionRepository.get_instructions_by_medicine(conn, id)
    # Get notes
    notes = await InstructionRepository.get_notes_by_medicine(conn, id)
    
    medicine_data = dict(medicine)
    medicine_data["schedules"] = schedules
    medicine_data["instructions"] = instructions
    medicine_data["notes"] = notes
    
    return success_response(medicine_data)

@router.patch("/{id}")
async def edit_medicine(
    id: UUID,
    data: MedicineEditSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
        
    await MedicineRepository.update_medicine(
        conn, id, name=data.name, medicine_type_id=data.medicine_type_id
    )
    # Trigger generation
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Medicine updated successfully")

@router.post("/{id}/pause")
async def pause_medicine(
    id: UUID,
    data: Optional[PauseMedicineSchema] = None,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    remark = data.remark if data else None
    await MedicineService.pause_medicine(conn, UUID(patient["patient_id"]), id, remark)
    # Update future events and notifications
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Medicine paused successfully")

@router.post("/{id}/resume")
async def resume_medicine(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    await MedicineService.resume_medicine(conn, UUID(patient["patient_id"]), id)
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Medicine resumed successfully")

@router.post("/{id}/finish")
async def finish_medicine(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    await MedicineService.finish_medicine(conn, UUID(patient["patient_id"]), id)
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Medicine finished successfully")

@router.post("/{id}/undo-finish")
async def undo_finish_medicine(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    await MedicineService.undo_finish_medicine(conn, UUID(patient["patient_id"]), id)
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Finished action undone successfully")

# ----------------- INSTRUCTIONS & NOTES -----------------

class InstructionCreateInputSchema(BaseModel):
    instruction_type: str  # "PAUSE", "RESUME", "STOP", "FINISH", "EXTEND_PAUSE"
    remark: Optional[str] = None

class NoteCreateInputSchema(BaseModel):
    note: str

@router.get("/{id}/instructions")
async def get_instructions(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    instructions = await InstructionRepository.get_instructions_by_medicine(conn, id)
    return success_response(instructions)

@router.post("/{id}/instructions")
async def create_instruction(
    id: UUID,
    data: InstructionCreateInputSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    
    async with conn.transaction():
        inst_id = await InstructionRepository.create_instruction(
            conn=conn,
            medicine_id=id,
            instruction_type=data.instruction_type,
            effective_from=datetime.now(),
            effective_until=None,
            remark=data.remark,
            created_by=UUID(patient["patient_id"])
        )
        await HistoryRepository.create_history(
            conn=conn,
            medicine_id=id,
            event_type="INSTRUCTION_ADDED",
            created_by=UUID(patient["patient_id"]),
            instruction_id=inst_id,
            new_data={"instruction_type": data.instruction_type, "remark": data.remark}
        )
    return success_response({"id": str(inst_id)}, message="Instruction added successfully")

@router.get("/{id}/notes")
async def get_notes(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    notes = await InstructionRepository.get_notes_by_medicine(conn, id)
    return success_response(notes)

@router.post("/{id}/notes")
async def create_note(
    id: UUID,
    data: NoteCreateInputSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    
    async with conn.transaction():
        note_id = await InstructionRepository.create_note(
            conn=conn,
            medicine_id=id,
            note=data.note,
            created_by=UUID(patient["patient_id"])
        )
        await HistoryRepository.create_history(
            conn=conn,
            medicine_id=id,
            event_type="NOTE_ADDED",
            created_by=UUID(patient["patient_id"]),
            note_id=note_id,
            new_data={"note": data.note}
        )
    return success_response({"id": str(note_id)}, message="Note added successfully")
