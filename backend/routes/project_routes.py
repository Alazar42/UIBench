from fastapi import APIRouter, Body, HTTPException, Depends, Header, UploadFile, File, Form
from ..database.connection import db_instance
from ..models.project import ProjectModel
from ..services.project_services import ProjectService
from ..services.auth_service import AuthService
from datetime import datetime
from pydantic import HttpUrl
import uuid
import os
import zipfile
import shutil

# Authentication dependency
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(token)

router = APIRouter(dependencies=[Depends(get_current_user)])

# Project service setup
projects_collection = db_instance.db["projects"]
project_service = ProjectService(projects_collection)

UPLOAD_DIR = "uploaded_projects"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/projects/")
async def create_project(
    title: str = Form(...),
    description: str = Form(""),
    url: HttpUrl = Form(None),
    file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    project_id = str(uuid.uuid4())
    owner_id = current_user["user_id"]
    creation_date = datetime.utcnow()
    project_directory = None

    if not url and not file:
        raise HTTPException(status_code=400, detail="Either a URL or a ZIP file must be provided.")

    if file:
        zip_filename = f"{project_id}_{file.filename}"
        zip_path = os.path.join(UPLOAD_DIR, zip_filename)

        try:
            with open(zip_path, "wb") as buffer:
                while contents := await file.read(1024 * 1024):
                    buffer.write(contents)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving uploaded file: {e}")
        finally:
            await file.close()

        extract_path = os.path.join(UPLOAD_DIR, project_id)
        os.makedirs(extract_path, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            project_directory = extract_path
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")

    project = ProjectModel(
        project_id=project_id,
        owner_id=owner_id,
        title=title,
        description=description,
        url=url,
        project_directory=project_directory,
        creation_date=creation_date
    )

    return project_service.create_project(project)


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
        raise HTTPException(
            status_code=403 if result["error"] == "Not authorized to delete this project" else 404,
            detail=result["error"]
        )
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
