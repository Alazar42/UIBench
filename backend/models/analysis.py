from pydantic import BaseModel
import uuid

class AnalysisResultModel(BaseModel):
    result_id: str = str(uuid.uuid4())
    design_id: str
    aesthetic_score: float
    accessibility_score: float
    performance_score: float
    usability_score: float
    analysis_date: str  # ISO format date string
    analysis_summary: str  # Summary of the analysis results
    detailed_report: str  # Link or path to the detailed report
    recommendations: str  # Recommendations based on the analysis results