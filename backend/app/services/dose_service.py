import asyncpg
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from app.repositories.event_repository import EventRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.patient_repository import PatientRepository

class DoseService:
    @staticmethod
    async def record_taken(
        conn: asyncpg.Connection,
        patient_id: UUID,
        dose_id: UUID,
        remark: Optional[str] = None
    ) -> dict:
        now_dt = datetime.now(timezone.utc)
        
        async with conn.transaction():
            # 1. Fetch dose
            dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            if not dose:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medication dose not found"
                )
                
            # Verify patient ownership
            # We can check event patient_id
            event = await conn.fetchrow("SELECT patient_id FROM medication_events WHERE id = $1::uuid;", dose["event_id"])
            if not event or event["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own this medication record"
                )

            # Concurrency check: must be in PENDING state to mark TAKEN
            if dose["status"] == "TAKEN":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This dose has already been recorded as taken."
                )

            # 2. Update status conditionally
            success = await EventRepository.update_dose_status(
                conn=conn,
                dose_id=dose_id,
                status="TAKEN",
                actual_taken_at=now_dt,
                status_changed_at=now_dt,
                status_remark=remark,
                expected_status=dose["status"]  # Ensures status hasn't changed since read
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Status changed by another process. Please refresh."
                )

            # 3. Create history
            prev_data = {
                "status": dose["status"],
                "actual_taken_at": dose["actual_taken_at"].isoformat() if dose["actual_taken_at"] else None
            }
            new_data = {
                "status": "TAKEN",
                "actual_taken_at": now_dt.isoformat()
            }
            
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=dose["medicine_id"],
                event_type="DOSE_TAKEN",
                created_by=patient_id,
                schedule_id=dose["schedule_id"],
                dose_id=dose_id,
                previous_data=prev_data,
                new_data=new_data,
                remark=remark
            )

            # 4. Remove notification record since it is taken
            await EventRepository.delete_notification(conn, dose["event_id"])
            
            # Fetch updated dose details to return
            updated_dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            return dict(updated_dose)

    @staticmethod
    async def record_skipped(
        conn: asyncpg.Connection,
        patient_id: UUID,
        dose_id: UUID,
        remark: Optional[str] = None
    ) -> dict:
        now_dt = datetime.now(timezone.utc)
        
        async with conn.transaction():
            # 1. Fetch dose
            dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            if not dose:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medication dose not found"
                )
                
            # Verify patient ownership
            event = await conn.fetchrow("SELECT patient_id FROM medication_events WHERE id = $1::uuid;", dose["event_id"])
            if not event or event["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own this medication record"
                )

            # Concurrency check
            if dose["status"] == "SKIPPED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This dose has already been skipped."
                )

            # 2. Update status conditionally
            success = await EventRepository.update_dose_status(
                conn=conn,
                dose_id=dose_id,
                status="SKIPPED",
                actual_taken_at=None,
                status_changed_at=now_dt,
                status_remark=remark,
                expected_status=dose["status"]
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Status changed by another process. Please refresh."
                )

            # 3. Create history
            prev_data = {
                "status": dose["status"],
                "actual_taken_at": dose["actual_taken_at"].isoformat() if dose["actual_taken_at"] else None
            }
            new_data = {
                "status": "SKIPPED",
                "actual_taken_at": None
            }
            
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=dose["medicine_id"],
                event_type="DOSE_SKIPPED",
                created_by=patient_id,
                schedule_id=dose["schedule_id"],
                dose_id=dose_id,
                previous_data=prev_data,
                new_data=new_data,
                remark=remark
            )

            # 4. Remove notification record since it is resolved
            await EventRepository.delete_notification(conn, dose["event_id"])
            
            updated_dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            return dict(updated_dose)

    @staticmethod
    async def record_corrected(
        conn: asyncpg.Connection,
        patient_id: UUID,
        dose_id: UUID,
        corrected_status: str,
        remark: Optional[str] = None
    ) -> dict:
        now_dt = datetime.now(timezone.utc)
        
        async with conn.transaction():
            # 1. Fetch dose
            dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            if not dose:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medication dose not found"
                )
                
            # Verify patient ownership
            event = await conn.fetchrow("SELECT patient_id FROM medication_events WHERE id = $1::uuid;", dose["event_id"])
            if not event or event["patient_id"] != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own this medication record"
                )

            if dose["status"] == corrected_status:
                # No change required
                return dict(dose)

            actual_taken_at = now_dt if corrected_status == "TAKEN" else None

            # 2. Update status conditionally
            success = await EventRepository.update_dose_status(
                conn=conn,
                dose_id=dose_id,
                status=corrected_status,
                actual_taken_at=actual_taken_at,
                status_changed_at=now_dt,
                status_remark=remark,
                expected_status=dose["status"]
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Status changed by another process. Please refresh."
                )

            # 3. Create history (DOSE_CORRECTED)
            prev_data = {
                "status": dose["status"],
                "actual_taken_at": dose["actual_taken_at"].isoformat() if dose["actual_taken_at"] else None
            }
            new_data = {
                "status": corrected_status,
                "actual_taken_at": actual_taken_at.isoformat() if actual_taken_at else None
            }
            
            await HistoryRepository.create_history(
                conn=conn,
                medicine_id=dose["medicine_id"],
                event_type="DOSE_CORRECTED",
                created_by=patient_id,
                schedule_id=dose["schedule_id"],
                dose_id=dose_id,
                previous_data=prev_data,
                new_data=new_data,
                remark=remark
            )

            # 4. Handle notification: if corrected back to PENDING, recreate notification
            if corrected_status == "PENDING":
                await EventRepository.create_notification(conn, dose["event_id"], dose["scheduled_at"])
            else:
                # Check if there are other pending doses in this event
                active_doses = await conn.fetch("""
                    SELECT COUNT(*) as cnt FROM event_doses
                    WHERE event_id = $1::uuid AND status = 'PENDING';
                """, dose["event_id"])
                if active_doses[0]["cnt"] == 0:
                    await EventRepository.delete_notification(conn, dose["event_id"])
            
            updated_dose = await EventRepository.get_event_dose_by_id(conn, dose_id)
            return dict(updated_dose)
