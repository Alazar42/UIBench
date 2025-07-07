from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Header
import asyncio

from backend.services import project_services
from ..database.connection import db_instance
from ..services.analysis_services import AnalysisService
from ..services.auth_service import AuthService

router = APIRouter(prefix="/users/me/projects/{project_id}/analysis", tags=["Analysis"])

analysis_collection = db_instance.db["analysis_results"]
project_collection = db_instance.db["projects"]  # Your projects collection
analysis_service = AnalysisService(analysis_collection, project_collection)

# Auth dependency
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(token)

@router.post("/")
async def create_analysis_background(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    project = db_instance.db["projects"].find_one({"project_id": project_id})
    if not project or project["owner_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")

    url = project.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Project does not have a URL to evaluate")

    response = await analysis_service.evaluate_and_store_async(
        url=url,
        project_id=project_id,
        owner_id=current_user["user_id"]
    )

    return response


@router.get("/{result_id}")
def get_analysis(result_id: str):
    result = analysis_service.get_analysis_by_id(result_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/")
def get_all_analyses(project_id: str):
    results = analysis_service.get_all_analyses_for_project(project_id)
    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
    return results

@router.delete("/{result_id}")
def delete_analysis(result_id: str):
    result = analysis_service.delete_analysis(result_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result