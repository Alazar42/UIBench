from pymongo.collection import Collection
from models.project import ProjectModel

class ProjectService:
    def __init__(self, collection):
        self.collection = collection

    def create_project(self, project):
        project_data = project.dict()
        self.collection.insert_one(project_data)

        # Add project ID to the user's projects list
        from database.connection import db_instance
        users_collection = db_instance.db["users"]
        users_collection.update_one(
            {"user_id": project.owner_id},
            {"$push": {"projects": project.project_id}}
        )

        return {"message": "Project created", "project_id": project.project_id}

    def get_project(self, project_id: str):
        project = self.collection.find_one({"project_id": project_id})
        if not project:
            return {"error": "Project not found"}
        project["_id"] = str(project["_id"])
        return project



