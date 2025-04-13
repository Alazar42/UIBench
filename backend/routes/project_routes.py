from fastapi import APIRouter, HTTPException, Depends, Header
from database.connection import db_instance
from models.project import ProjectModel
from services.project_services import ProjectService
from services.auth_service import AuthService
from datetime import datetime
import uuid

router = APIRouter()
projects_collection = db_instance.db["projects"]
project_service = ProjectService(projects_collection)

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(token)

@router.post("/projects/")
def create_project(project: ProjectModel, current_user: dict = Depends(get_current_user)):
    # Override sensitive fields
    project.project_id = str(uuid.uuid4())
    project.owner_id = current_user["user_id"]
    project.creation_date = datetime.utcnow()
    result = project_service.create_project(project)
    return result

@router.get("/projects/{project_id}")
def get_project(project_id: str):
    project = project_service.get_project(project_id)
    if "error" in project:
        raise HTTPException(status_code=404, detail=project["error"])
    project.pop("_id", None)
    return project

