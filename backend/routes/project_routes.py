from fastapi import APIRouter, HTTPException
from database.connection import db_instance
from models.project import ProjectModel
from services.project_services import ProjectService

router = APIRouter()
projects_collection = db_instance.db["projects"]
project_service = ProjectService(projects_collection)

@router.post("/projects/")
def create_project(project: ProjectModel):
    result = project_service.create_project(project)
    return result

@router.get("/projects/{project_id}")
def get_project(project_id: str):
    project = project_service.get_project(project_id)
    if "error" in project:
        raise HTTPException(status_code=404, detail=project["error"])
    return project
