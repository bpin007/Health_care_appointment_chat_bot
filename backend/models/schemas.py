from pydantic import BaseModel, EmailStr
from typing import Optional, List

class AppointmentRequest(BaseModel):
    appointment_type: str
    date: str
    start_time: str
    doctor_id: int
    reason: str
    patient_name: str
    patient_email: EmailStr
    patient_phone: str

class TimeSlot(BaseModel):
    start_time: str
    end_time: str
    available: bool
    doctor_id: Optional[int]
    doctor_name: Optional[str]
    specialization: Optional[str]
    duration: int

class AvailabilityResponse(BaseModel):
    date: str
    available_slots: List[TimeSlot]

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: dict
    session_id: str
