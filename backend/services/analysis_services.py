from pymongo.collection import Collection
from models.analysis import AnalysisResultModel

class AnalysisService:
    def __init__(self, analysis_collection: Collection):
        self.analysis_collection = analysis_collection

    def store_analysis(self, analysis: AnalysisResultModel):
        self.analysis_collection.insert_one(analysis.dict())
        return {"message": "Analysis result stored", "result": analysis}

    def get_analysis(self, design_id: str):
        result = self.analysis_collection.find_one({"design_id": design_id}, {"_id": 0})
        return result if result else {"error": "Analysis result not found"}
