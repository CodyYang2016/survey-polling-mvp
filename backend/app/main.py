from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import sessions, admin, export, respondents

app = FastAPI(title="Polling Survey API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper prefixes
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(respondents.router, prefix="/api/v1", tags=["respondents"])

@app.get("/")
def read_root():
    return {"message": "Polling Survey API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}