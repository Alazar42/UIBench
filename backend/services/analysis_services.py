from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from ..models.analysis import AnalysisResultModel
from fastapi.encoders import jsonable_encoder
from datetime import datetime
import uuid
from ..models.project import ProjectModel
from pymongo.collection import Collection
import asyncio
from asyncio import Semaphore

executor = ThreadPoolExecutor()  # Use ThreadPoolExecutor to avoid pickling issues
executor_lock = Lock()

# Limit the number of concurrent processes to 2
process_semaphore = Semaphore(2)

class AnalysisService:
    def __init__(self, analysis_collection, project_collection):
        self.analysis_collection = analysis_collection
        self.project_collection = project_collection

    async def evaluate_and_store_async(self, url: str, project_id: str, owner_id: str):
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

        # Check if a process can start immediately or needs to wait
        if process_semaphore._value > 0:
            asyncio.create_task(self._run_evaluation_with_semaphore(result_id, url, project_id, owner_id))
            return {
                "message": "Evaluation started in background",
                "result_id": result_id,
                "queued_at": now
            }
        else:
            return {
                "message": "Evaluation queued due to process limit",
                "result_id": result_id,
                "queued_at": now
            }

    async def _run_evaluation_with_semaphore(self, result_id, url, project_id, owner_id):
        async with process_semaphore:
            await self._run_evaluation_and_store(result_id, url, project_id, owner_id)

    async def _run_evaluation_and_store(self, result_id, url, project_id, owner_id):
        print("Evaluation started...")

        try:
            # Run the evaluation in an asynchronous context
            from core.evaluators.website_evaluator import WebsiteEvaluator
            from playwright.async_api import async_playwright
            import json

            def recursive_parse(data):
                """Recursively parse JSON strings into Python dictionaries."""
                if isinstance(data, str):
                    try:
                        parsed = json.loads(data)
                        return recursive_parse(parsed)
                    except json.JSONDecodeError:
                        return data
                elif isinstance(data, dict):
                    return {key: recursive_parse(value) for key, value in data.items()}
                elif isinstance(data, list):
                    return [recursive_parse(item) for item in data]
                return data

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    await page.goto(url, timeout=60000)
                    html = await page.content()
                    body_text = await page.inner_text("body")

                    evaluator = WebsiteEvaluator(
                        root_url=url,
                        max_subpages=100,
                        max_depth=3,
                        concurrency=5,
                        custom_criteria={},
                        page=page  # Pass the page object
                    )

                    results = await evaluator.evaluate_page(html, body_text)

                    # Ensure results are awaited if they are coroutines
                    if asyncio.iscoroutine(results):
                        results = await results

                    # Recursively parse and reformat the results
                    results = recursive_parse(results)

                    update_data = {
                        "status": "completed",
                        "result": results,  # Save the entire JSON result
                        "analysis_date": datetime.utcnow()
                    }

                    # Update analysis result with the response JSON
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
                finally:
                    await browser.close()
        except Exception as e:
            print(f"Error during evaluation: {e}")
            self.analysis_collection.update_one(
                {"result_id": result_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )

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