from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

DOCTOR_SECRET_PIN = "doc123"

# --- SCHEMAS ---
class PatientLoginRequest(BaseModel):
    name: str = Field(..., example="Hamza Khan")
    phone: str = Field(..., example="+1-555-0199")

class DoctorLoginRequest(BaseModel):
    doctor_name: str = Field(..., example="Dr. Emily Watson")
    pin: str = Field(..., example="doc123")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    phone: str = ""

# --- PATIENT LOGIN ---
@router.post("/patient-login", response_model=AuthResponse)
async def patient_login(req: PatientLoginRequest):
    """Logs in a patient and issues a verified Patient Token."""
    token_data = {
        "sub": req.phone,
        "name": req.name.strip(),
        "role": "patient",
        "phone": req.phone.strip()
    }
    token = create_access_token(token_data)
    return AuthResponse(
        access_token=token,
        role="patient",
        name=req.name.strip(),
        phone=req.phone.strip()
    )

# --- DOCTOR LOGIN ---
@router.post("/doctor-login", response_model=AuthResponse)
async def doctor_login(req: DoctorLoginRequest):
    """Authenticates an attending physician against the Clinic Security PIN."""
    if req.pin != DOCTOR_SECRET_PIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Doctor Security PIN. Physician access denied."
        )

    token_data = {
        "sub": req.doctor_name.strip(),
        "name": req.doctor_name.strip(),
        "role": "doctor",
        "phone": ""
    }
    token = create_access_token(token_data)
    return AuthResponse(
        access_token=token,
        role="doctor",
        name=req.doctor_name.strip()
    )