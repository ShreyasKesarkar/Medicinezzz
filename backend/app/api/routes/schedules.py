from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, date, time, timedelta
from typing import Optional, List
from app.database import db
from app.security.auth import get_current_patient
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.history_repository import HistoryRepository
from app.services.scheduler_service import SchedulerService
from app.schemas.schedule import ScheduleCreateSchema, ScheduleUpdateSchema
from app.utils.response import success_response

router = APIRouter()

async def trigger_event_generation(conn, patient_id: str):
    today_local = date.today()
    start_gen = today_local - timedelta(days=7)
    end_gen = today_local + timedelta(days=30)
    await SchedulerService.generate_events_for_patient(conn, UUID(patient_id), start_gen, end_gen)

@router.get("/medicines/{medicine_id}/schedules")
async def get_medicine_schedules(
    medicine_id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
        
    schedules = await ScheduleRepository.get_schedules_by_medicine_id(conn, medicine_id)
    return success_response(schedules)

@router.post("/medicines/{medicine_id}/schedules")
async def create_schedule(
    medicine_id: UUID,
    data: ScheduleCreateSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
        
    try:
        hour, minute = map(int, data.schedule_time.split(":"))
        sched_time = time(hour, minute)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid schedule_time format. Must be HH:MM"
        )

    async with conn.transaction():
        # Create schedule
        schedule_id = await ScheduleRepository.create_schedule(conn, medicine_id, status="ACTIVE")
        
        # Create version 1
        await ScheduleRepository.create_schedule_version(
            conn=conn,
            schedule_id=schedule_id,
            version_number=1,
            schedule_time=sched_time,
            dosage_amount=data.dosage_amount,
            dosage_unit_id=data.dosage_unit_id,
            frequency=data.frequency,
            weekday=data.weekday,
            interval_days=data.interval_days,
            start_date=data.start_date,
            planned_end_date=data.planned_end_date,
            effective_from=datetime.now(),
            change_remark=data.remark
        )
        
        # Create history
        await HistoryRepository.create_history(
            conn=conn,
            medicine_id=medicine_id,
            event_type="SCHEDULE_CREATED",
            created_by=UUID(patient["patient_id"]),
            schedule_id=schedule_id,
            new_data={
                "schedule_id": str(schedule_id),
                "frequency": data.frequency,
                "schedule_time": data.schedule_time
            },
            remark=data.remark
        )
        
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response({"id": str(schedule_id)}, message="Schedule created successfully")

@router.patch("/schedules/{id}")
async def edit_schedule(
    id: UUID,
    data: ScheduleUpdateSchema,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    schedule = await ScheduleRepository.get_schedule_by_id(conn, id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
        
    medicine = await MedicineRepository.get_medicine_by_id(conn, schedule["medicine_id"])
    if not medicine or medicine["patient_id"] != UUID(patient["patient_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    async with conn.transaction():
        last_ver = await ScheduleRepository.get_last_version_number(conn, id)
        new_ver_num = last_ver + 1
        
        # Parse schedule time
        sched_time = schedule["schedule_time"]
        if data.schedule_time:
            try:
                hour, minute = map(int, data.schedule_time.split(":"))
                sched_time = time(hour, minute)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid schedule_time format. Must be HH:MM"
                )

        # Fallbacks to active version fields
        dosage_amount = data.dosage_amount if data.dosage_amount is not None else float(schedule["dosage_amount"])
        dosage_unit_id = data.dosage_unit_id if data.dosage_unit_id is not None else schedule["dosage_unit_id"]
        frequency = data.frequency if data.frequency is not None else schedule["frequency"]
        weekday = data.weekday if data.weekday is not None else schedule["weekday"]
        interval_days = data.interval_days if data.interval_days is not None else schedule["interval_days"]
        start_date = data.start_date if data.start_date is not None else schedule["start_date"]
        planned_end_date = data.planned_end_date if data.planned_end_date is not None else schedule["planned_end_date"]
        
        # Insert a new version with incremented version number
        await ScheduleRepository.create_schedule_version(
            conn=conn,
            schedule_id=id,
            version_number=new_ver_num,
            schedule_time=sched_time,
            dosage_amount=dosage_amount,
            dosage_unit_id=dosage_unit_id,
            frequency=frequency,
            weekday=weekday,
            interval_days=interval_days,
            start_date=start_date,
            planned_end_date=planned_end_date,
            effective_from=datetime.now(),
            change_remark=data.remark
        )
        
        # Log history
        await HistoryRepository.create_history(
            conn=conn,
            medicine_id=schedule["medicine_id"],
            event_type="SCHEDULE_UPDATED",
            created_by=UUID(patient["patient_id"]),
            schedule_id=id,
            previous_data={
                "version_number": schedule["version_number"],
                "frequency": schedule["frequency"],
                "schedule_time": schedule["schedule_time"].isoformat() if isinstance(schedule["schedule_time"], time) else str(schedule["schedule_time"])
            },
            new_data={
                "version_number": new_ver_num,
                "frequency": frequency,
                "schedule_time": sched_time.isoformat()
            },
            remark=data.remark
        )
        
    await trigger_event_generation(conn, patient["patient_id"])
    return success_response(message="Schedule version updated successfully")
