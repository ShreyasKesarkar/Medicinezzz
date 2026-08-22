from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum

class ScheduleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    INACTIVE = "INACTIVE"

class FrequencyType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    EVERY_N_DAYS = "EVERY_N_DAYS"

class ScheduleVersionSchema(BaseModel):
    id: UUID
    schedule_id: UUID
    version_number: int
    schedule_time: time
    dosage_amount: float
    dosage_unit_id: UUID
    frequency: FrequencyType
    weekday: Optional[int] = None
    interval_days: Optional[int] = None
    start_date: date
    planned_end_date: Optional[date] = None
    effective_from: datetime
    effective_until: Optional[datetime] = None
    change_remark: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ScheduleSchema(BaseModel):
    id: UUID
    medicine_id: UUID
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime
    
    # Optional active version pre-loaded
    active_version: Optional[ScheduleVersionSchema] = None
    versions: List[ScheduleVersionSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class ScheduleCreateSchema(BaseModel):
    schedule_time: str  # Format: "HH:MM"
    dosage_amount: float
    dosage_unit_id: UUID
    frequency: FrequencyType
    weekday: Optional[int] = None
    interval_days: Optional[int] = None
    start_date: date
    planned_end_date: Optional[date] = None
    remark: Optional[str] = None  # Change/Creation remark

class ScheduleUpdateSchema(BaseModel):
    schedule_time: Optional[str] = None
    dosage_amount: Optional[float] = None
    dosage_unit_id: Optional[UUID] = None
    frequency: Optional[FrequencyType] = None
    weekday: Optional[int] = None
    interval_days: Optional[int] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    remark: Optional[str] = None  # Saved to schedule_versions.change_remark and history
class ScheduleDetailsSchema(BaseModel):
    id: UUID
    medicine_id: UUID
    medicine_name: str
    status: ScheduleStatus
    active_version: ScheduleVersionSchema
    
    model_config = ConfigDict(from_attributes=True)
