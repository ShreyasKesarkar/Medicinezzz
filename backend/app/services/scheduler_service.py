import asyncpg
from uuid import UUID
from datetime import datetime, date, time, timedelta, timezone
import zoneinfo
from typing import List, Optional
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.event_repository import EventRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.instruction_repository import InstructionRepository
from app.repositories.medicine_repository import MedicineRepository

LOCAL_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

class SchedulerService:
    @staticmethod
    def get_occurrence_dates(version: dict, start_gen: date, end_gen: date) -> List[date]:
        anchor = version["start_date"]
        freq = version["frequency"]
        planned_end = version["planned_end_date"]
        
        # Clip range to schedule bounds
        actual_end = end_gen
        if planned_end:
            actual_end = min(end_gen, planned_end)
            
        actual_start = max(start_gen, anchor)
        occurrences = []
        
        if freq == "DAILY":
            curr = anchor
            while curr <= actual_end:
                if curr >= actual_start:
                    occurrences.append(curr)
                curr += timedelta(days=1)
                
        elif freq == "WEEKLY":
            target_wd = version["weekday"]
            if target_wd is None:
                # Default to the same weekday as start_date
                target_wd = anchor.isoweekday()
                
            curr = anchor
            # Find the first occurrence of the target weekday on or after anchor
            days_diff = target_wd - curr.isoweekday()
            if days_diff < 0:
                days_diff += 7
            curr += timedelta(days=days_diff)
            
            while curr <= actual_end:
                if curr >= actual_start:
                    occurrences.append(curr)
                curr += timedelta(days=7)
                
        elif freq == "EVERY_N_DAYS":
            n = version["interval_days"]
            if not n or n <= 0:
                n = 1
            curr = anchor
            while curr <= actual_end:
                if curr >= actual_start:
                    occurrences.append(curr)
                curr += timedelta(days=n)
                
        return occurrences

    @staticmethod
    async def generate_events_for_patient(
        conn: asyncpg.Connection,
        patient_id: UUID,
        start_date_local: date,
        end_date_local: date
    ) -> int:
        # Fetches all active schedules for patient
        schedules = await ScheduleRepository.get_active_schedules_for_patient(conn, patient_id)
        
        doses_created = 0
        
        # We run transaction for inserting all generated events/doses
        async with conn.transaction():
            # Check pause instructions active for the patient's medicines
            # We can retrieve all pause instructions for patient medicines to avoid multiple queries
            instructions = await conn.fetch("""
                SELECT * FROM medication_instructions
                WHERE created_by = $1::uuid AND instruction_type IN ('PAUSE', 'RESUME', 'FINISH');
            """, patient_id)
            
            for s in schedules:
                # Find all versions of this schedule to check versions effective at scheduled times
                # But since get_active_schedules_for_patient returns current active version, we can use it
                # For future timeline generation, the current version is the one active.
                # If there are older versions, we can retrieve them if we need historical generation,
                # but typically get_schedule_version_at_time will be used if needed.
                # Let's generate dates based on version
                occ_dates = SchedulerService.get_occurrence_dates(s, start_date_local, end_date_local)
                
                for occ_date in occ_dates:
                    # Combine occurrence date and schedule time in Asia/Kolkata
                    local_dt = datetime.combine(occ_date, s["schedule_time"]).replace(tzinfo=LOCAL_TZ)
                    utc_dt = local_dt.astimezone(timezone.utc)
                    
                    # 1. Determine if medicine is paused or finished at this scheduled time
                    is_paused = False
                    is_finished = False
                    
                    # Check instructions timeline
                    med_instructions = [i for i in instructions if i["medicine_id"] == s["medicine_id"]]
                    # Sort by effective_from to find status at utc_dt
                    med_instructions.sort(key=lambda x: x["effective_from"])
                    
                    status_at_time = "ACTIVE"
                    for inst in med_instructions:
                        if inst["effective_from"] <= utc_dt:
                            if inst["instruction_type"] == "PAUSE":
                                status_at_time = "PAUSED"
                            elif inst["instruction_type"] == "RESUME":
                                status_at_time = "ACTIVE"
                            elif inst["instruction_type"] == "FINISH":
                                status_at_time = "FINISHED"
                                
                    if status_at_time == "PAUSED":
                        is_paused = True
                    elif status_at_time == "FINISHED":
                        is_finished = True
                        
                    # If finished at this time, we skip generating doses entirely
                    if is_finished:
                        continue
                        
                    # 2. Get or create medication_events at this scheduled time
                    event = await EventRepository.get_event_by_time(conn, patient_id, utc_dt)
                    if not event:
                        event_id = await EventRepository.create_event(conn, patient_id, utc_dt)
                    else:
                        event_id = event["id"]
                        
                    # 3. Check if event dose already exists
                    dose = await EventRepository.get_event_dose_by_schedule_and_event(conn, s["schedule_id"], event_id)
                    if not dose:
                        status_str = "NOT_REQUIRED" if is_paused else "PENDING"
                        status_remark = "Paused" if is_paused else None
                        
                        await EventRepository.create_event_dose(
                            conn=conn,
                            event_id=event_id,
                            medicine_id=s["medicine_id"],
                            schedule_id=s["schedule_id"],
                            schedule_version_id=s["version_id"],
                            dosage_amount=s["dosage_amount"],
                            dosage_unit_id=s["dosage_unit_id"],
                            scheduled_at=utc_dt,
                            status=status_str
                        )
                        doses_created += 1
                        
            # 4. Generate/Update event notifications for pending events
            # Fetch all events of this patient in the generation range
            events = await conn.fetch("""
                SELECT * FROM medication_events
                WHERE patient_id = $1::uuid AND scheduled_at >= $2 AND scheduled_at <= $3;
            """, patient_id, 
               datetime.combine(start_date_local, time(0,0)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
               datetime.combine(end_date_local, time(23,59)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc))
               
            for e in events:
                # Check active doses in this event
                active_doses = await conn.fetch("""
                    SELECT COUNT(*) as cnt FROM event_doses
                    WHERE event_id = $1::uuid AND status = 'PENDING';
                """, e["id"])
                
                # If there are active doses, schedule or update notification
                if active_doses[0]["cnt"] > 0:
                    await EventRepository.create_notification(conn, e["id"], e["scheduled_at"])
                else:
                    # If no pending doses, remove notification record
                    await EventRepository.delete_notification(conn, e["id"])
                    
        return doses_created
