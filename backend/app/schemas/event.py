from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DoseStatus(str, Enum):
    PENDING = "PENDING"
    TAKEN = "TAKEN"
    MISSED = "MISSED"
    SKIPPED = "SKIPPED"
    NOT_REQUIRED = "NOT_REQUIRED"

class EventDoseSchema(BaseModel):
    id: UUID
    event_id: UUID
    medicine_id: UUID
    schedule_id: UUID
    schedule_version_id: UUID
    dosage_amount: float
    dosage_unit_id: UUID
    scheduled_at: datetime
    status: DoseStatus
    actual_taken_at: Optional[datetime] = None
    status_changed_at: Optional[datetime] = None
    status_remark: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MedicationEventSchema(BaseModel):
    id: UUID
    patient_id: UUID
    scheduled_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Detailed schemas for API output

class DoseDetailsSchema(BaseModel):
    id: UUID
    event_id: UUID
    medicine_id: UUID
    medicine_name: str
    medicine_type_name: Optional[str] = None
    schedule_id: UUID
    schedule_version_id: UUID
    dosage_amount: float
    dosage_unit_name: str
    scheduled_at: datetime
    status: DoseStatus
    actual_taken_at: Optional[datetime] = None
    status_changed_at: Optional[datetime] = None
    status_remark: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ClusteredEventSchema(BaseModel):
    event_id: UUID
    scheduled_at: datetime
    doses: List[DoseDetailsSchema]
    
    model_config = ConfigDict(from_attributes=True)

class TakeDoseSchema(BaseModel):
    remark: Optional[str] = None

class SkipDoseSchema(BaseModel):
    remark: str = "Skipped"  # Skipped might require remark, but let's make it optional or default

class CorrectDoseSchema(BaseModel):
    status: DoseStatus  # The corrected status (e.g. TAKEN, SKIPPED, PENDING)
    remark: Optional[str] = None
