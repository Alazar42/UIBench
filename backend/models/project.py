from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional

class ProjectModel(BaseModel):
    project_id: Optional[str] = None  # Generated in code
    name: str
    url: Optional[HttpUrl] = None  # URL of the project
    project_directory: Optional[str] = None  # Path to the project directory on the server
    creation_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    owner_id: Optional[str] = None
    description: Optional[str] = ""

    analysis_result_ids: List[str] = []  # Link to AnalysisResultModel
    feedback_ids: List[str] = []  # Link to user feedback/comments

    is_public: bool = False
    tags: List[str] = []

    def dict(self, *args, **kwargs):
        # Convert HttpUrl to string for MongoDB compatibility
        project_dict = super().model_dump(*args, **kwargs)
        project_dict['url'] = str(self.url)  # Convert the HttpUrl to a string
        return project_dict
