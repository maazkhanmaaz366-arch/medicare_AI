from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os 
from core.config import settings
from api.clinic.service import seed_doctor_if_empty
from api.agent.ws_router import ws_router
from api.auth.router import router as auth_router

#1. Lifespan: Auto seed doctors on startup
@asynccontextmanager
async def lifespan(app:FastAPI):
    print("[Medicare AI] starting up...")
    await seed_doctor_if_empty()
    yield
    print("[Medicare AI] shuting down...")

# 2. FastAPI Application

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

#3. Cors Configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# 4.static files (UI)

os.makedirs('static', exist_ok=True)
app.mount('/static',StaticFiles(directory='static'), name = 'static')

# 5. Register Routers 
app.include_router(ws_router)
app.include_router(auth_router)

@app.get('/')
async def root():
    return {
        'status':'healthy',
        'service':settings.PROJECT_NAME,
        'version':settings.VERSION,
        'chat_ui':"/static/clinic_chat.html"
    }
