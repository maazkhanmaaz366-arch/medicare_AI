from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DoctorBase(BaseModel):

    name:str=Field(...,example='Dr.Emily watson')
    specialty:str=Field(...,example='cardiology')
    consultation_fee:float=Field(..., ge=0, example=150.0)
    available_days:List[str]=Field(...,example=['Monday','sunday','friday'])
    available_hours:str=Field(...,example='09:00 AM - 02:00')
    bio:str = Field(...,example="Board-certifide Cardiologist specialized")
    rating:float=Field(default=4.9, ge=0.0, le=5.0)

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id:str


class AppointmentCreate(BaseModel):
    doctor_id:str=Field(...,example="65123...")
    doctor_name:str=Field(...,example="Dr.Maaz Khan")
    patient_name:str=Field(...,example="Fawad Khan")
    patient_phone:str=Field(...,example="+1-555-0199")
    appointment_date:str=Field(...,example="2026-11-25")
    time_slot:str=Field(...,example="10:00 AM")
    symptoms:str=Field(...,example="Frequent chest tightness and shortness of breath")
    is_critical_procedure:bool=Field(default=False, description="set True for surgeries or Invasive procedures requiring doctor  HITL approval")


class AppointmentResponse(BaseModel):
    id:str
    appointment_ref:str
    doctor_name:str
    patient_name:str
    appointment_date:str
    time_slot:str
    symptoms:str
    status:str
    is_critical_procedure:bool
    created_at:str