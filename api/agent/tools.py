from langchain_core.tools import tool
from typing import Optional
from ddgs import DDGS
from api.clinic.service import search_doctor, book_appointment, cancel_appointment, get_doctor_appointments
from api.agent.rag import query_clinical_guidlines

@tool
async def search_doctors_tool(specialty:Optional[str] = None,max_fee:Optional[float] = None, days:Optional[str] =None) -> str:
    """Search the clinic roster of doctor.
    -speciality: Medical field like 'cardiology', Pediatric neurology
    -max_fee: Maximuim consultation fee the patient is willing to pay.
    -day: Day of the week the patient wants to visit e.g Monday, Saturday
    
    """

    doctors  = await search_doctor(specialty=specialty, max_fee=max_fee, day=days)
    if not doctors:
        return f"No doctors found matching criteria (speciality:{specialty}, Max:{max_fee}, days:{days} )"

    lines = [f"Found {len(doctors)} matching doctor(s):"]

    for d in doctors:
        lines.append(
            f"-{d['name']} | Specialty: {d['specialty']} | Fee: ${d['consultation_fee']}"
            f"Available: {', '.join(d['available_days'])} ({d['available_hours']}) | Rating: {d['rating']}"
            
        )
    return '\n'.join(lines)

@tool
async def book_appointment_tool(
    doctor_name:str,
    patient_name:str,
    patient_phone:str,
    appointment_date:str,
    time_slot:str,
    symptoms:str,
    is_critical_procedure:bool=False) ->str:

    """
    Book an appointment with a clinic doctor.
    - doctor_name: Full name of the doctor (e.g. 'Dr. Emily watson')
    - patient_name: Name of the patient booking the consultation.
    - patient_phone: Contact telephone number.
    - appointment_date: Date formated as YYY-MM-DD.
    - time_slot: Time formated e.g '10:00 AM', '02:00 PM'
    - symptoms: Brief description of patient condition or reason for visit
    - is_critical_procedure: True if booking a surgery biosby or invasive procedure requiring doctor approval
    
    """

    payload = {
        'doctor_name':doctor_name,
        'patient_name':patient_name,
        'patient_phone':patient_phone,
        'appointment_date': appointment_date,
        'time_slot':time_slot,
        "symptoms":symptoms,
        'is_critical_procedure':is_critical_procedure
    }

    result = await book_appointment(payload)
    if 'error' in result:
        return f"Booking Failed: {result['error']}"
    
    return(
          f"✅ Appointment Successfully Scheduled!\n"
        f"- Reference Number: {result['appointment_ref']}\n"
        f"- Doctor: {result['doctor_name']}\n"
        f"- Patient: {result['patient_name']}\n"
        f"- Date & Time: {result['appointment_date']} at {result['time_slot']}\n"
        f"- Status: {result['status'].upper()}\n"
        f"- Notes: Please arrive 15 minutes early with photo ID and insurance card."
    )


@tool
async def cancel_appointment_tool(appointment_ref:str, reason:str="Patient requested") -> str:
    """
    Cancel an existing appointment using its refrence code (e.g APT-B31F7).
    """
    res = await cancel_appointment(appointment_ref)
    if 'error' in res:
        return f"cancellation Failed: {res['error']}"
    
    return (
          f"✅ Appointment {res['appointment_ref']} has been CANCELLED.\n"
        f"- Doctor: {res['doctor_name']}\n"
        f"- Scheduled Time Was: {res['appointment_date']} at {res['time_slot']}\n"
        f"- Reason: {reason}"
    )


@tool
async def online_medical_search_tool(query:str) ->str:
    """Search the live web live generals medical information, drug interaction, or external research"""

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results = 3))
            if not results:
                return f"no online results found fo {query}"
            lines = [f"Online medical search result for {query}"]
            for r in results:
                lines.append(f"- **{r.get('title')}**:{r.get('body')} ({r.get('href')})")
            return '\n'.join(lines)
    except Exception as e:
        return f"search error: {str(e)}"

@tool
async def clinical_guidlines_tool(query:str) -> str:
    """Search official clinic preparation rules, fasting guidlines, cancellation policies and insurance coverage.
       Use this whenever a patient asks about pre-test prep, eating/drinking before blood tests or clinic policies
    """
    return query_clinical_guidlines(query)

@tool
async def view_doctor_schedule_tool(doctor_name: str, date: Optional[str] = None) -> str:
    """
    View all active scheduled patient consultations for a specific doctor.
    - doctor_name: The name of the doctor (e.g. 'Dr. Emily Watson' or 'Dr. Marcus Vance').
    - date: Optional specific date filter (YYYY-MM-DD).
    Only available when a doctor or clinic administrator asks to view their schedule.
    """
    appointments = await get_doctor_appointments(doctor_name=doctor_name, date=date)
    if not appointments:
        return f"No active appointments found for {doctor_name}" + (f" on {date}." if date else ".")

    lines = [f"📅 Schedule for {doctor_name} ({len(appointments)} appointment(s)):"]
    for apt in appointments:
        crit_badge = " [CRITICAL PROCEDURE]" if apt.get("is_critical_procedure") else ""
        lines.append(
            f"- Ref: {apt['appointment_ref']} | Patient: {apt['patient_name']} | "
            f"Date: {apt['appointment_date']} at {apt['time_slot']} | "
            f"Status: {apt['status'].upper()}{crit_badge} | Symptoms: {apt['symptoms']}"
        )
    return "\n".join(lines)
