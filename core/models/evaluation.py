from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class EvaluationRequest(BaseModel):
    """Request model for website evaluation."""
    url: HttpUrl
    crawl_subpages: Optional[bool] = False
    max_subpages: Optional[int] = None
    max_depth: Optional[int] = 10
    custom_criteria: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EvaluationResult(BaseModel):
    """Model for individual page evaluation results."""
    url: str
    score: float
    defects: List[str]
    details: Dict[str, Any]

class AggregatedScores(BaseModel):
    """Model for aggregated evaluation scores."""
    accessibility: float
    performance: float
    seo: float
    security: float
    usability: float
    code_quality: float

class EnhancedEvaluationReport(BaseModel):
    """Comprehensive evaluation report model."""
    homepage: str
    pages: List[Dict[str, Any]]
    summary: Dict[str, Any]
    recommendations: List[str]
    accessibility_score: float
    performance_score: float
    seo_score: float
    security_score: float
    usability_score: float
    code_quality_score: float
    defect_details: Dict[str, Any]
    detailed_report: Dict[str, Any]
    learning_resources: Dict[str, Any]
    language_score: float
    ux_enhanced: Dict[str, Any]
    cognitive_load_score: float
    evaluated_at: datetime = Field(default_factory=datetime.utcnow) 