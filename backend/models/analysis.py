from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import uuid

class AnalysisResultModel(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Relationship
    project_id: str = None  # Injected during request, The project this analysis belongs to.

    # Evaluation Metrics
    aesthetic_score: float
    accessibility_score: float
    performance_score: float
    usability_score: float

    # Metadata
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    analysis_summary: str
    detailed_report: HttpUrl
    recommendations: str
