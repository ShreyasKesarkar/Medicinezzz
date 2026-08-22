from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum

class MedicineStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    FINISHED = "FINISHED"

class MedicineTypeSchema(BaseModel):
    id: UUID
    name: str
    is_system_defined: bool
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DosageUnitSchema(BaseModel):
    id: UUID
    name: str
    is_system_defined: bool
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MedicineSchema(BaseModel):
    id: UUID
    patient_id: UUID
    name: str
    medicine_type_id: Optional[UUID] = None
    status: MedicineStatus
    previous_medicine_id: Optional[UUID] = None
    finished_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested objects helper
    medicine_type: Optional[MedicineTypeSchema] = None
    
    model_config = ConfigDict(from_attributes=True)

class MedicineCreateSchema(BaseModel):
    name: str
    medicine_type_id: Optional[UUID] = None
    medicine_type_name: Optional[str] = None  # To support creating custom type on the fly
    
    dosage_amount: float = Field(..., gt=0)
    dosage_unit_id: Optional[UUID] = None
    dosage_unit_name: Optional[str] = None  # To support creating custom unit on the fly
    
    # Schedule info
    schedule_time: str  # Format: "HH:MM" (local time)
    frequency: str  # "DAILY", "WEEKLY", "EVERY_N_DAYS"
    weekday: Optional[int] = None  # 1 (Monday) to 7 (Sunday)
    interval_days: Optional[int] = None
    start_date: date
    planned_end_date: Optional[date] = None
    
    # Optional details
    instruction_remark: Optional[str] = None  # Saved to medication_instructions
    note: Optional[str] = None  # Saved to medicine_notes
    remark: Optional[str] = None  # For creation audit trail remark

class MedicineEditSchema(BaseModel):
    name: Optional[str] = None
    medicine_type_id: Optional[UUID] = None
    medicine_type_name: Optional[str] = None
    remark: Optional[str] = None  # Saved to history log

class PauseMedicineSchema(BaseModel):
    pause_days: Optional[int] = None  # If none, pause indefinitely. If set, time-bound instructions
    remark: Optional[str] = None

class ResumeMedicineSchema(BaseModel):
    remark: Optional[str] = None

class FinishMedicineSchema(BaseModel):
    remark: Optional[str] = None
