from fastapi import APIRouter, HTTPException, Path
from database.connection import db_instance
from models.analysis import AnalysisResultModel
from services.analysis_services import AnalysisService
from datetime import datetime

router = APIRouter(prefix="/users/me/projects/{project_id}/analysis", tags=["Analysis"])

analysis_collection = db_instance.db["analysis_results"]
analysis_service = AnalysisService(analysis_collection)


@router.post("/")
def create_analysis(project_id: str, analysis: AnalysisResultModel):
    # Inject project_id into the model
    analysis.project_id = project_id
    analysis.analysis_date = datetime.utcnow()  # Ensure timestamp is current
    return analysis_service.store_analysis(analysis)


@router.get("/")
def get_latest_analysis(project_id: str):
    result = analysis_collection.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("analysis_date", -1).limit(1)

    result_list = list(result)
    if not result_list:
        raise HTTPException(status_code=404, detail="No analysis results found for this project")
    return result_list[0]
