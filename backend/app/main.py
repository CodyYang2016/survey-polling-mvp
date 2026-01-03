from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sessions, admin, export
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Polling Survey AI Moderator", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(sessions.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Polling Survey AI Moderator API", "version": "1.0.0", "status": "operational"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
