from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from enum import Enum

class HistoryEventType(str, Enum):
    MEDICINE_CREATED = "MEDICINE_CREATED"
    MEDICINE_UPDATED = "MEDICINE_UPDATED"
    SCHEDULE_CREATED = "SCHEDULE_CREATED"
    SCHEDULE_UPDATED = "SCHEDULE_UPDATED"
    SCHEDULE_ENDED = "SCHEDULE_ENDED"
    DOSE_CREATED = "DOSE_CREATED"
    DOSE_TAKEN = "DOSE_TAKEN"
    DOSE_MISSED = "DOSE_MISSED"
    DOSE_SKIPPED = "DOSE_SKIPPED"
    DOSE_NOT_REQUIRED = "DOSE_NOT_REQUIRED"
    DOSE_CORRECTED = "DOSE_CORRECTED"
    PAUSE_STARTED = "PAUSE_STARTED"
    PAUSE_EXTENDED = "PAUSE_EXTENDED"
    MEDICINE_RESUMED = "MEDICINE_RESUMED"
    MEDICINE_STOPPED = "MEDICINE_STOPPED"
    MEDICINE_FINISHED = "MEDICINE_FINISHED"
    FINISH_UNDONE = "FINISH_UNDONE"
    NOTE_ADDED = "NOTE_ADDED"
    NOTE_CORRECTED = "NOTE_CORRECTED"
    INSTRUCTION_ADDED = "INSTRUCTION_ADDED"
    INSTRUCTION_CORRECTED = "INSTRUCTION_CORRECTED"

class MedicineHistorySchema(BaseModel):
    id: UUID
    medicine_id: UUID
    event_type: HistoryEventType
    event_time: datetime
    schedule_id: Optional[UUID] = None
    dose_id: Optional[UUID] = None
    instruction_id: Optional[UUID] = None
    note_id: Optional[UUID] = None
    previous_data: Optional[Any] = None
    new_data: Optional[Any] = None
    remark: Optional[str] = None
    created_by: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class HistoryLogSchema(BaseModel):
    id: UUID
    medicine_id: UUID
    medicine_name: str
    event_type: HistoryEventType
    event_time: datetime
    remark: Optional[str] = None
    previous_data: Optional[Any] = None
    new_data: Optional[Any] = None
    
    model_config = ConfigDict(from_attributes=True)
