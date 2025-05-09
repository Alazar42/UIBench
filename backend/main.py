from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.debug_router import debug_router
from .routes.auth_routes import router as auth_router
from .routes.project_routes import router as project_router
from .routes.analysis_routes import router as analysis_router
from .database.connection import db_instance
from contextlib import asynccontextmanager

app = FastAPI(title="UIBench API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router)
app.include_router(project_router, prefix="/users/me")
app.include_router(analysis_router)
app.include_router(debug_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    db_instance.close()

@app.get("/")
def home():
    return {"message": "Welcome to the UIBench API"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API status.
    
    Returns:
        Dict with API status information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
