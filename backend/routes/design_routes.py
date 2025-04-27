from fastapi import APIRouter, HTTPException
from database.connection import db_instance
from models.design import DesignModel
from services.project_services import ProjectService

router = APIRouter()
designs_collection = db_instance.db["designs"]
projects_collection = db_instance.db["projects"]
project_service = ProjectService(projects_collection)

@router.post("/designs/")
def create_design(design: DesignModel):
    # Check if project exists
    project = project_service.get_project(design.project_id)
    if "error" in project:
        raise HTTPException(status_code=404, detail="Project not found")

    designs_collection.insert_one(design.dict())
    return {"message": "Design added successfully", "design": design}
