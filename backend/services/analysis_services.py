from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from ..models.analysis import AnalysisResultModel
from fastapi.encoders import jsonable_encoder
from core.evaluators.website_evaluator import WebsiteEvaluator
from datetime import datetime
import uuid
from ..models.project import ProjectModel
from pymongo.collection import Collection
from core.evaluators.website_evaluator import WebsiteEvaluator
import asyncio

executor = ThreadPoolExecutor(max_workers=2)
executor_lock = Lock()

class AnalysisService:
    def __init__(self, analysis_collection, project_collection):
        self.analysis_collection = analysis_collection
        self.project_collection = project_collection

    def evaluate_and_store_async(self, url: str, project_id: str, owner_id: str):
        result_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Insert initial "in progress" doc
        self.analysis_collection.insert_one({
            "result_id": result_id,
            "project_id": project_id,
            "user_id": owner_id,
            "url": url,
            "status": "in progress",
            "score": None,
            "details": None,
            "analysis_date": now
        })

        self.project_collection.update_one(
            {"project_id": project_id},
            {
                "$push": {"analysis_result_ids": result_id},
                "$set": {"last_updated": datetime.utcnow()}
            }
        )

        with executor_lock:
            executor.submit(
                self._run_evaluation_and_store,
                result_id=result_id,
                url=url,
                project_id=project_id,
                owner_id=owner_id
            )

        return result_id  # Useful if caller wants to track it


    def _run_evaluation_and_store(self, result_id, url, project_id, owner_id):

        print("Evaluation started...")
        

        evaluator = WebsiteEvaluator(
            root_url=url,
            max_subpages=100,
            max_depth=3,
            concurrency=5,
            custom_criteria={}
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(evaluator.evaluate(crawl=True))

        update_data = {
            "status": "completed",
            "score": results.get("score"),
            "details": results.get("details"),
            "analysis_date": datetime.utcnow()
        }

        # Update analysis result
        self.analysis_collection.update_one(
            {"result_id": result_id},
            {"$set": update_data}
        )

        # Update project doc
        self.project_collection.update_one(
            {"project_id": project_id},
            {
                "$push": {"analysis_result_ids": result_id},
                "$set": {"last_updated": datetime.utcnow()}
            }
        )
        print(f"✅ Evaluation completed and saved for project: {project_id}")

    def get_analysis_by_id(self, result_id: str):
        result = self.analysis_collection.find_one({"result_id": result_id}, {"_id": 0})
        if result:
            return result
        return {"error": "Analysis result not found"}

    def get_all_analyses_for_project(self, project_id: str):
        results = list(self.analysis_collection.find({"project_id": project_id}, {"_id": 0}))
        if results:
            return results
        return {"error": "No analyses found for this project"}

    def delete_analysis(self, result_id: str):
        result = self.analysis_collection.delete_one({"result_id": result_id})
        if result.deleted_count == 1:
            return {"message": "Analysis result deleted"}
        return {"error": "Analysis result not found"}