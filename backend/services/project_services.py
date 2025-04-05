from pymongo.collection import Collection
from models.project import ProjectModel

class ProjectService:
    def __init__(self, projects_collection: Collection):
        self.projects_collection = projects_collection

    def create_project(self, project: ProjectModel):
        self.projects_collection.insert_one(project.dict())
        return {"message": "Project created successfully", "project": project}

    def get_project(self, project_id: str):
        project = self.projects_collection.find_one({"project_id": project_id}, {"_id": 0})
        return project if project else {"error": "Project not found"}
