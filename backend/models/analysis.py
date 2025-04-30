from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import uuid
from typing import Optional

class AnalysisResultModel(BaseModel):
    result_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

    # Relationship
    project_id: Optional[str] = None  # Injected during request, The project this analysis belongs to.

    # Evaluation Metrics
    aesthetic_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    performance_score: Optional[float] = None
    usability_score: Optional[float] = None

    # Metadata
    analysis_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    analysis_summary: Optional[str] = None
    detailed_report: Optional[HttpUrl] = None
    recommendations: Optional[str] = None
