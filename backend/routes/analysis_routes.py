from fastapi import APIRouter, HTTPException
from database.connection import db_instance
from models.analysis import AnalysisResultModel

router = APIRouter()
analysis_collection = db_instance.db["analysis_results"]

@router.post("/analysis/")
def create_analysis(analysis: AnalysisResultModel):
    analysis_collection.insert_one(analysis.dict())
    return {"message": "Analysis result stored", "result": analysis}

@router.get("/analysis/{design_id}")
def get_analysis(design_id: str):
    result = analysis_collection.find_one({"design_id": design_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result
