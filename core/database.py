
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings 

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]

doctors_collection = db['doctors']
appointments_collection = db['appointments']
patient_collection = db['patients']
