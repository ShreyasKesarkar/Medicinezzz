from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Optional

class UserProfileSchema(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PatientSchema(BaseModel):
    id: UUID
    user_id: UUID
    date_of_birth: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class CurrentPatientSchema(BaseModel):
    patient_id: UUID
    user_id: UUID
    full_name: Optional[str] = None
    timezone: str
    
    model_config = ConfigDict(from_attributes=True)
