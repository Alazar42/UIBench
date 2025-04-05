from pymongo.collection import Collection
from models.design import DesignModel

class DesignService:
    def __init__(self, designs_collection: Collection):
        self.designs_collection = designs_collection

    def create_design(self, design: DesignModel):
        self.designs_collection.insert_one(design.dict())
        return {"message": "Design added successfully", "design": design}

    def get_design(self, design_id: str):
        design = self.designs_collection.find_one({"design_id": design_id}, {"_id": 0})
        return design if design else {"error": "Design not found"}
