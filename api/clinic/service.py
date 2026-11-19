from bson import ObjectId
from datetime import datetime
import uuid
from core.database import doctors_collection, appointments_collection

def format_doctor(doc:dict) ->dict:
    return{
        "id":str(doc['_id']),
        'name':doc.get('name'),
        'specialty':doc.get('specialty'),
        "consultation_fee":doc.get('consultation_fee'),
        'available_days':doc.get('available_days'),
        'available_hours':doc.get('available_hours'),
        'bio':doc.get('bio'),
        'rating':doc.get('rating',4.8)
    }

def format_appointments(doc:dict) -> dict:
    return {
        'id':str(doc['_id']),
        "appointment_ref": doc.get('appointment_ref'),
        'doctor_name':doc.get('doctor_name'),
        'patient_name':doc.get('patient_name'),
        'appointment_date':doc.get('appointment_date'),
        'time_slot':doc.get('time_slot'),
        'symptoms':doc.get('symptoms'),
        'status':doc.get('status','confirmed'),
        'is_critical_procedure':doc.get('is_critical_procedure',False)
        ,'created_at': doc.get('created_at')
    }


async def seed_doctor_if_empty():
    """Seeds a divers clinical staff of top doctors if collection is empty"""

    count = await doctors_collection.count_documents({})
    if count > 0:
        return 
    
    doctors_seed = [
        {
            "name": "Dr. Emily Watson",
            "specialty": "Cardiology",
            "consultation_fee": 150.0,
            "available_days": ["Monday", "Wednesday", "Friday"],
            "available_hours": "09:00 AM - 02:00 PM",
            "bio": "Senior Cardiologist specializing in preventive cardiology, hypertension, and arrhythmias.",
            "rating": 4.9
        },
        {
            "name": "Dr. Marcus Vance",
            "specialty": "Orthopedics",
            "consultation_fee": 130.0,
            "available_days": ["Tuesday", "Thursday", "Saturday"],
            "available_hours": "10:00 AM - 04:00 PM",
            "bio": "Orthopedic Surgeon expert in sports injuries, knee pain, and spine mobility.",
            "rating": 4.8
        },
        {
            "name": "Dr. Sarah Lin",
            "specialty": "Dermatology",
            "consultation_fee": 110.0,
            "available_days": ["Monday", "Tuesday", "Thursday"],
            "available_hours": "08:30 AM - 01:30 PM",
            "bio": "Consultant Dermatologist treating skin rashes, acne, psoriasis, and cosmetic dermatology.",
            "rating": 4.9
        },
        {
            "name": "Dr. Robert Chen",
            "specialty": "Pediatrics",
            "consultation_fee": 95.0,
            "available_days": ["Monday", "Wednesday", "Saturday"],
            "available_hours": "09:00 AM - 03:00 PM",
            "bio": "Compassionate pediatrician with 15+ years care for infant care, childhood fevers, and vaccines.",
            "rating": 5.0
        },
        {
            "name": "Dr. Aisha Malik",
            "specialty": "Neurology",
            "consultation_fee": 180.0,
            "available_days": ["Wednesday", "Friday", "Sunday"],
            "available_hours": "11:00 AM - 05:00 PM",
            "bio": "Expert Neurologist treating chronic migraines, epilepsy, and nerve disorders.",
            "rating": 4.9
        }
    ]
    await doctors_collection.insert_many(doctors_seed)


async def search_doctor(specialty:str=None, max_fee:float=None, day:str=None) -> list:
    query = {}
    if specialty:
        query['specialty'] = {'$regex':specialty, '$options':'i'}
    
    if day:
        query['available_days'] = {"$in":[day.capitalize()]}
    if max_fee:
        query['consultation_fee'] = {"$lte":max_fee}
    
    cursor = doctors_collection.find(query)
    docs = await cursor.to_list(length=20)
    return [format_doctor(doc) for doc in docs]


async def book_appointment(data:dict) -> dict:
    conflict = await appointments_collection.find_one({
        'doctor_name':data.get('doctor_name'),
        'appointment_date':data.get('appointment_date'),
        'time_slot':data.get('time_slot'),
        'status':{"$ne":'cancelled'}
    })

    if conflict:
        return{"error":f"Slot {data.get('time_slot')} on {data.get('appointment_date')} is already booked with {data.get('doctor_name')}"}
    
    ref  = f"APT-{uuid.uuid4().hex[:5].upper()}"
    status = "pending_doctor_approval" if data.get('is_critical_procedure', False) else 'confirmed'
    record = {
        **data,
        'appointment_ref':ref,
        'status':status,
        'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S' )

    }

    res = await appointments_collection.insert_one(record)
    record['_id'] = res.inserted_id
    return format_appointments(record)


async def cancel_appointment(appointment_ref_or_id:str)->dict:
    query = {}
    if ObjectId.is_valid(appointment_ref_or_id):
        query = {'_id': ObjectId(appointment_ref_or_id)}
    else:
        query = {'appointment_ref':appointment_ref_or_id.upper()}
    
    res = await appointments_collection.find_one_and_update(query,{"$set":{'status':'cancelled', 'updated_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}},return_document=True)
    if not res:
        return {'error':f"No appointment found with refrence {appointment_ref_or_id}"}
    return format_appointments(res)

async def get_doctor_appointments(doctor_name: str, date: str = None) -> list:
    """Returns active appointments booked for a specific doctor."""
    query = {
        "doctor_name": {"$regex": doctor_name, "$options": "i"},
        "status": {"$ne": "cancelled"}
    }
    if date:
        query["appointment_date"] = date
    cursor = appointments_collection.find(query)
    docs = await cursor.to_list(length=50)
    return [format_appointments(d) for d in docs]
