from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base, init_db
from app.db import models
from app.core.config import settings

# Initialize database tables
init_db()

app = FastAPI(
    title="MOSAIC Browser Agent API",
    description="Backend API for the MOSAIC universal personal browser agent",
    version="1.0.0"
)

# CORS middleware configuration for frontend local dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "env_mode": settings.ENV_MODE,
        "database_connected": True,
        "gemini_api_configured": bool(settings.GEMINI_API_KEY)
    }

from app.api import memory, activity, websites, documents, agent

app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(activity.router, prefix="/api/activity", tags=["activity"])
app.include_router(websites.router, prefix="/api/learned-websites", tags=["learned-websites"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])



