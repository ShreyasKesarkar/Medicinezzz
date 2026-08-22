import asyncpg
from uuid import UUID
from datetime import datetime, date, time
from typing import Optional, List
from fastapi import HTTPException, status
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.instruction_repository import InstructionRepository
from app.repositories.event_repository import EventRepository
from app.schemas.medicine import MedicineCreateSchema, MedicineStatus
from app.schemas.schedule import FrequencyType

class MedicineService:
    @staticmethod
    async def create_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        data: MedicineCreateSchema
    ) -> UUID:
        async with conn.transaction():
            # 1. Get or create type
            type_id = data.medicine_type_id
            if not type_id and data.medicine_type_name:
                type_id = await MedicineRepository.get_or_create_type(conn, patient_id, data.medicine_type_name)
                
            # 2. Get or create unit
            unit_id = data.dosage_unit_id
            if not unit_id and data.dosage_unit_name:
                unit_id = await MedicineRepository.get_or_create_unit(conn, patient_id, data.dosage_unit_name)
            elif not unit_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dosage unit ID or name must be provided"
                )

            # 3. Create medicine
            medicine_id = await MedicineRepository.create_medicine(
                conn, patient_id, data.name, type_id, status="ACTIVE"
            )
            
            # 4. Create schedule
            schedule_id = await ScheduleRepository.create_schedule(conn, medicine_id, status="ACTIVE")
            
            # 5. Parse schedule time
            try:
                hour, minute = map(int, data.schedule_time.split(":"))
                sched_time = time(hour, minute)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid schedule_time format. Must be HH:MM"
                )

            # 6. Create schedule version
            version_id = await ScheduleRepository.create_schedule_version(
                conn=conn,
                schedule_id=schedule_id,
                version_number=1,
                schedule_time=sched_time,
                dosage_amount=data.dosage_amount,
                dosage_unit_id=unit_id,
                frequency=data.frequency,
                weekday=data.weekday,
                interval_days=data.interval_days,
                start_date=data.start_date,
                planned_end_date=data.planned_end_date,
                effective_from=datetime.now()
            )
            
            # 7. Create optional note
            note_id = None
            if data.note:
                note_id = await InstructionRepository.create_note(conn, medicine_id, data.note, patient_id)
                await HistoryRepository.create_history(
                    conn=conn,
                    medicine_id=medicine_id,
                    event_type="NOTE_ADDED",
                    created_by=patient_id,
                    note_id=note_id,
                    new_data={"note": data.note}
                )

            # 8. Create optional instruction
            instruction_id = None
            if data.instruction_remark:
                instruction_id = await InstructionRepository.create_instruction(
                    conn=conn,
                    medicine_id=medicine_id,
                    instruction_type="RESUME",  # Standard instruction
                    effective_from=datetime.now(),
                    effective_until=None,
                    remark=data.instruction_remark,
                    created_by=patient_id
                )
                await HistoryRepository.create_history(
                    conn=conn,
                    medicine_id=medicine_id,
                    event_type="INSTRUCTION_ADDED",
                    created_by=patient_id,
                    instruction_id=instruction_id,
                    new_data={"remark": data.instruction_remark}
                )

            # 9. Create histories
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="MEDICINE_CREATED",
                created_by=patient_id,
                new_data={"name": data.name, "medicine_type_id": str(type_id) if type_id else None},
                remark=data.remark
            )
            
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="SCHEDULE_CREATED",
                created_by=patient_id,
                schedule_id=schedule_id,
                new_data={
                    "schedule_id": str(schedule_id),
                    "version_number": 1,
                    "frequency": data.frequency,
                    "schedule_time": data.schedule_time
                }
            )
            
            return medicine_id

    @staticmethod
    async def pause_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        medicine_id: UUID,
        remark: Optional[str] = None
    ) -> None:
        async with conn.transaction():
            # 1. Fetch medicine
            medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
            if not medicine or medicine["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found"
                )
                
            if medicine["status"] == "PAUSED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medicine is already paused"
                )
                
            if medicine["status"] == "FINISHED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot pause a finished medicine"
                )

            # 2. Add instruction
            instruction_id = await InstructionRepository.create_instruction(
                conn=conn,
                medicine_id=medicine_id,
                instruction_type="PAUSE",
                effective_from=datetime.now(),
                effective_until=None,
                remark=remark,
                created_by=patient_id
            )
            
            # 3. Update status
            await MedicineRepository.update_medicine(
                conn, medicine_id, status="PAUSED"
            )
            
            # Update future event doses
            await conn.execute("""
                UPDATE event_doses
                SET status = 'NOT_REQUIRED', status_changed_at = now(), status_remark = 'Paused'
                WHERE medicine_id = $1::uuid AND status = 'PENDING' AND scheduled_at >= now();
            """, medicine_id)
            
            # 4. Create history
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="PAUSE_STARTED",
                created_by=patient_id,
                instruction_id=instruction_id,
                previous_data={"status": medicine["status"]},
                new_data={"status": "PAUSED"},
                remark=remark
            )

    @staticmethod
    async def resume_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        medicine_id: UUID,
        remark: Optional[str] = None
    ) -> None:
        async with conn.transaction():
            # 1. Fetch medicine
            medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
            if not medicine or medicine["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found"
                )
                
            if medicine["status"] != "PAUSED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medicine is not paused"
                )

            # 2. Add instruction
            instruction_id = await InstructionRepository.create_instruction(
                conn=conn,
                medicine_id=medicine_id,
                instruction_type="RESUME",
                effective_from=datetime.now(),
                effective_until=None,
                remark=remark,
                created_by=patient_id
            )
            
            # 3. Update status
            await MedicineRepository.update_medicine(
                conn, medicine_id, status="ACTIVE"
            )
            
            # Restore future paused doses
            await conn.execute("""
                UPDATE event_doses
                SET status = 'PENDING', status_changed_at = now(), status_remark = NULL
                WHERE medicine_id = $1::uuid AND status = 'NOT_REQUIRED' AND status_remark = 'Paused' AND scheduled_at >= now();
            """, medicine_id)
            
            # 4. Create history
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="MEDICINE_RESUMED",
                created_by=patient_id,
                instruction_id=instruction_id,
                previous_data={"status": "PAUSED"},
                new_data={"status": "ACTIVE"},
                remark=remark
            )

    @staticmethod
    async def finish_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        medicine_id: UUID,
        remark: Optional[str] = None
    ) -> None:
        async with conn.transaction():
            # 1. Fetch medicine
            medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
            if not medicine or medicine["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found"
                )
                
            if medicine["status"] == "FINISHED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medicine is already finished"
                )

            # 2. Add instruction
            instruction_id = await InstructionRepository.create_instruction(
                conn=conn,
                medicine_id=medicine_id,
                instruction_type="FINISH",
                effective_from=datetime.now(),
                effective_until=None,
                remark=remark,
                created_by=patient_id
            )
            
            # 3. Update status
            await MedicineRepository.update_medicine(
                conn, medicine_id, status="FINISHED", finished_at=datetime.now()
            )
            
            # Set future pending or paused doses of this finished medicine to NOT_REQUIRED
            await conn.execute("""
                UPDATE event_doses
                SET status = 'NOT_REQUIRED', status_changed_at = now(), status_remark = 'Finished'
                WHERE medicine_id = $1::uuid AND status IN ('PENDING', 'NOT_REQUIRED') AND scheduled_at >= now();
            """, medicine_id)
            
            # 4. Create history
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="MEDICINE_FINISHED",
                created_by=patient_id,
                instruction_id=instruction_id,
                previous_data={"status": medicine["status"]},
                new_data={"status": "FINISHED", "finished_at": datetime.now().isoformat()},
                remark=remark
            )

    @staticmethod
    async def undo_finish_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        medicine_id: UUID,
        remark: Optional[str] = None
    ) -> None:
        async with conn.transaction():
            # 1. Fetch medicine
            medicine = await MedicineRepository.get_medicine_by_id(conn, medicine_id)
            if not medicine or medicine["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found"
                )
                
            if medicine["status"] != "FINISHED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medicine is not finished"
                )

            # 2. Add instruction
            instruction_id = await InstructionRepository.create_instruction(
                conn=conn,
                medicine_id=medicine_id,
                instruction_type="RESUME",
                effective_from=datetime.now(),
                effective_until=None,
                remark=remark,
                created_by=patient_id
            )
            
            # 3. Update status
            await conn.execute("""
                UPDATE medicines
                SET status = 'ACTIVE', finished_at = NULL, updated_at = now()
                WHERE id = $1::uuid;
            """, medicine_id)
            
            # Restore future finished doses
            await conn.execute("""
                UPDATE event_doses
                SET status = 'PENDING', status_changed_at = now(), status_remark = NULL
                WHERE medicine_id = $1::uuid AND status = 'NOT_REQUIRED' AND status_remark = 'Finished' AND scheduled_at >= now();
            """, medicine_id)
            
            # 4. Create history
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=medicine_id,
                event_type="FINISH_UNDONE",
                created_by=patient_id,
                instruction_id=instruction_id,
                previous_data={"status": "FINISHED", "finished_at": medicine["finished_at"].isoformat() if medicine["finished_at"] else None},
                new_data={"status": "ACTIVE"},
                remark=remark
            )
