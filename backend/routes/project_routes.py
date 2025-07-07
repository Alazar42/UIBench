from fastapi import APIRouter, Body, HTTPException, Depends, Header
from ..database.connection import db_instance
from ..models.project import ProjectModel
from ..services.project_services import ProjectService
from ..services.auth_service import AuthService
from datetime import datetime
import uuid

# Define the authentication dependency
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(token)

# Apply the dependency globally to all routes in this router
router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

projects_collection = db_instance.db["projects"]
project_service = ProjectService(projects_collection)

@router.post("/projects/")
def create_project(project: ProjectModel, current_user: dict = Depends(get_current_user)):
    project.project_id = str(uuid.uuid4())
    project.owner_id = current_user["user_id"]
    project.creation_date = datetime.utcnow()
    result = project_service.create_project(project)
    return result

@router.get("/projects/{project_id}")
def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = project_service.get_project(project_id)
    if "error" in project:
        raise HTTPException(status_code=404, detail=project["error"])
    project.pop("_id", None)
    return project

@router.get("/projects/")
def list_user_projects(current_user: dict = Depends(get_current_user)):
    return project_service.list_projects(current_user["user_id"])

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    result = project_service.delete_project(project_id, current_user["user_id"])
    if "error" in result:
        raise HTTPException(status_code=403 if result["error"] == "Not authorized to delete this project" else 404, detail=result["error"])
    return result

@router.put("/projects/{project_id}")
def update_project(
    project_id: str,
    update_data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    result = project_service.update_project(project_id, current_user["user_id"], update_data)
    if "error" in result:
        raise HTTPException(
            status_code=403 if result["error"] == "Not authorized to update this project" else 404,
            detail=result["error"]
        )
    return result