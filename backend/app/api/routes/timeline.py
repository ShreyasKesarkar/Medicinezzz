from fastapi import APIRouter, Depends, Query
from uuid import UUID
from datetime import datetime, date, time, timedelta, timezone
import zoneinfo
from typing import Optional
from app.database import db
from app.security.auth import get_current_patient
from app.repositories.event_repository import EventRepository
from app.services.scheduler_service import SchedulerService
from app.utils.response import success_response

router = APIRouter()
LOCAL_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

@router.get("")
async def get_timeline(
    date_str: Optional[str] = Query(None, alias="date"),
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    # Parse target date
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except Exception:
            target_date = datetime.now(LOCAL_TZ).date()
    else:
        target_date = datetime.now(LOCAL_TZ).date()
        
    patient_uuid = UUID(patient["patient_id"])
    
    # 1. Trigger rolling window generation (7 days past, 30 days future from target date)
    start_gen = target_date - timedelta(days=7)
    end_gen = target_date + timedelta(days=30)
    await SchedulerService.generate_events_for_patient(conn, patient_uuid, start_gen, end_gen)
    
    # 2. Query all doses for target date
    start_dt = datetime.combine(target_date, time.min).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    end_dt = datetime.combine(target_date, time.max).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    
    doses = await EventRepository.get_doses_for_patient(conn, patient_uuid, start_dt, end_dt)
    
    # 3. Cluster doses by event_id
    clusters = {}
    for d in doses:
        evt_id = str(d["event_id"])
        if evt_id not in clusters:
            # Convert UTC scheduled_at back to local time string for the user UI
            local_time_dt = d["scheduled_at"].astimezone(LOCAL_TZ)
            clusters[evt_id] = {
                "event_id": evt_id,
                "scheduled_at": local_time_dt.isoformat(),
                "doses": []
            }
            
        local_dose_dt = d["scheduled_at"].astimezone(LOCAL_TZ)
        clusters[evt_id]["doses"].append({
            "id": str(d["dose_id"]),
            "event_id": evt_id,
            "medicine_id": str(d["medicine_id"]),
            "medicine_name": d["medicine_name"],
            "medicine_type_name": d["medicine_type_name"],
            "schedule_id": str(d["schedule_id"]),
            "schedule_version_id": str(d["schedule_version_id"]),
            "dosage_amount": float(d["dosage_amount"]),
            "dosage_unit_name": d["dosage_unit_name"],
            "scheduled_at": local_dose_dt.isoformat(),
            "status": d["status"],
            "actual_taken_at": d["actual_taken_at"].astimezone(LOCAL_TZ).isoformat() if d["actual_taken_at"] else None,
            "status_changed_at": d["status_changed_at"].astimezone(LOCAL_TZ).isoformat() if d["status_changed_at"] else None,
            "status_remark": d["status_remark"]
        })
        
    # Sort clusters chronologically
    sorted_clusters = sorted(clusters.values(), key=lambda x: x["scheduled_at"])
    
    return success_response(sorted_clusters)
