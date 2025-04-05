from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional

class DesignModel(BaseModel):
    design_id: str = str(uuid.uuid4())
    project_id: str
    version: str
    upload_date: datetime = datetime.utcnow()
    analysis_result: Optional[str] = None  # AnalysisResult ID
