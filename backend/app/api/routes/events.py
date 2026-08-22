from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import zoneinfo
from app.database import db
from app.security.auth import get_current_patient
from app.utils.response import success_response

router = APIRouter()
LOCAL_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

@router.get("/{id}")
async def get_event(
    id: UUID,
    patient: dict = Depends(get_current_patient),
    conn = Depends(db.get_conn)
):
    event = await conn.fetchrow("""
        SELECT * FROM medication_events 
        WHERE id = $1::uuid AND patient_id = $2::uuid;
    """, id, UUID(patient["patient_id"]))
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication event not found"
        )
        
    doses = await conn.fetch("""
        SELECT d.*, m.name as medicine_name, u.name as dosage_unit_name, t.name as medicine_type_name
        FROM event_doses d
        JOIN medicines m ON d.medicine_id = m.id
        LEFT JOIN medicine_types t ON m.medicine_type_id = t.id
        JOIN dosage_units u ON d.dosage_unit_id = u.id
        WHERE d.event_id = $1::uuid;
    """, id)
    
    event_data = dict(event)
    event_data["scheduled_at"] = event["scheduled_at"].astimezone(LOCAL_TZ).isoformat()
    
    doses_list = []
    for d in doses:
        d_dict = dict(d)
        d_dict["id"] = str(d_dict["id"])
        d_dict["event_id"] = str(d_dict["event_id"])
        d_dict["medicine_id"] = str(d_dict["medicine_id"])
        d_dict["schedule_id"] = str(d_dict["schedule_id"])
        d_dict["schedule_version_id"] = str(d_dict["schedule_version_id"])
        d_dict["dosage_unit_id"] = str(d_dict["dosage_unit_id"])
        d_dict["scheduled_at"] = d_dict["scheduled_at"].astimezone(LOCAL_TZ).isoformat()
        
        if d_dict["actual_taken_at"]:
            d_dict["actual_taken_at"] = d_dict["actual_taken_at"].astimezone(LOCAL_TZ).isoformat()
        if d_dict["status_changed_at"]:
            d_dict["status_changed_at"] = d_dict["status_changed_at"].astimezone(LOCAL_TZ).isoformat()
            
        doses_list.append(d_dict)
        
    event_data["doses"] = doses_list
    return success_response(event_data)
