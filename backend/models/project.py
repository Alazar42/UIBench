from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import List

class ProjectModel(BaseModel):
    project_id: str = str(uuid.uuid4())
    name: str
    creation_date: datetime = datetime.utcnow()
    owner_id: str  # User ID
    designs: List[str] = []  # List of Design IDs
    description: str = None  # Optional description