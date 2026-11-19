
from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict


ENV_PATH = Path(__file__).resolve().parent.parent/'.env'

class Settings(BaseSettings):
    PROJECT_NAME:str="MediCare AI - clinic Operation Copilot"
    VERSION:str = '1.0.0'
    MONGO_URL:str='mongodb://localhost:27017'
    DATABASE_NAME:str='medicare_db'
    GROQ_API_KEY:str
    SECRET_KEY:str
    ALGORITHM:str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int=60
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH)
        ,env_file_encoding='utf-8'
        ,extra='ignore'
    )

settings = Settings()