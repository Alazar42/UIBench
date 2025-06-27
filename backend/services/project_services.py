import os
from pymongo.collection import Collection
from ..models.project import ProjectModel
from ..database.connection import db_instance

class ProjectService:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create_project(self, project: ProjectModel):
        project_data = project.dict()
        self.collection.insert_one(project_data)

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

    def list_projects(self, owner_id: str):
        projects = self.collection.find({"owner_id": owner_id})
        result = []
        for project in projects:
            project["_id"] = str(project["_id"])
            result.append(project)
            result[-1].pop("_id", None)
        return result

    def delete_project(self, project_id: str, owner_id: str):
        project = self.collection.find_one({"project_id": project_id})
        if not project:
            return {"error": "Project not found"}

        if project["owner_id"] != owner_id:
            return {"error": "Not authorized to delete this project"}

        self.collection.delete_one({"project_id": project_id})

        users_collection = db_instance.db["users"]
        users_collection.update_one(
            {"user_id": owner_id},
            {"$pull": {"projects": project_id}}
        )

        return {"message": "Project deleted"}

    def update_project(self, project_id: str, owner_id: str, update_data: dict):
        project = self.collection.find_one({"project_id": project_id})
        if not project:
            return {"error": "Project not found"}

        if project["owner_id"] != owner_id:
            return {"error": "Not authorized to update this project"}

        restricted_fields = {"project_id", "owner_id", "_id", "creation_date"}
        update_data = {k: v for k, v in update_data.items() if k not in restricted_fields}

        if not update_data:
            return {"error": "No valid fields to update"}

        self.collection.update_one(
            {"project_id": project_id},
            {"$set": update_data}
        )

        return {"message": "Project updated"}
