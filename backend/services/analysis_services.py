from pymongo.collection import Collection
from fastapi.encoders import jsonable_encoder  # To handle complex types serialization
from models.analysis import AnalysisResultModel

class AnalysisService:
    def __init__(self, analysis_collection: Collection):
        self.analysis_collection = analysis_collection

    def store_analysis(self, analysis: AnalysisResultModel):
        # Use jsonable_encoder to ensure proper serialization of complex types
        encoded_analysis = jsonable_encoder(analysis)
        self.analysis_collection.insert_one(encoded_analysis)
        return {"message": "Analysis result stored", "result": analysis}

    def get_analysis_by_result_id(self, result_id: str):
        # Find analysis by result_id and exclude _id from the result
        result = self.analysis_collection.find_one({"result_id": result_id}, {"_id": 0})
        if result:
            return result
        return {"error": "Analysis result not found"}

    def get_analyses_for_project(self, project_id: str):
        # Retrieve all analyses for a given project
        results = list(self.analysis_collection.find({"project_id": project_id}, {"_id": 0}))
        if results:
            return results
        return {"error": "No analyses found for this project"}

    def delete_analysis(self, result_id: str):
        # Delete analysis based on result_id
        result = self.analysis_collection.delete_one({"result_id": result_id})
        if result.deleted_count == 1:
            return {"message": "Analysis result deleted"}
        return {"error": "Analysis result not found"}

    def update_analysis(self, result_id: str, update_data: dict):
        # Update analysis based on result_id and the provided update data
        result = self.analysis_collection.update_one(
            {"result_id": result_id},
            {"$set": update_data}
        )
        if result.matched_count == 1:
            return {"message": "Analysis result updated"}
        return {"error": "Analysis result not found"}
