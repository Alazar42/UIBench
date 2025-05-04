from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.project_routes import router as project_router
from routes.design_routes import router as design_router
from routes.analysis_routes import router as analysis_router
from database.connection import db_instance
from contextlib import asynccontextmanager

app = FastAPI(title="UIBench API", version="1.0.0")

app.include_router(auth_router)
app.include_router(project_router, prefix="/users/me")
app.include_router(design_router)
app.include_router(analysis_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    db_instance.close()

@app.get("/")
def home():
    return {"message": "Welcome to the UIBench API"}
