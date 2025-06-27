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

executor = ThreadPoolExecutor()
executor_lock = Lock()

# Limit the number of concurrent processes
process_semaphore = Semaphore(2)

class AnalysisService:
    def __init__(self, analysis_collection, project_collection):
        self.analysis_collection = analysis_collection
        self.project_collection = project_collection

    async def evaluate_and_store_async(self, url: str, project_dir: str, project_id: str, owner_id: str):
        source = None

        # Determine source based on input priority
        if url and url.strip() != "":
            source = url.strip()
        elif project_dir and project_dir.strip() != "":
            source = project_dir.strip()
        else:
            raise ValueError("Either 'url' or 'project_dir' must be provided")

        result_id = str(uuid.uuid4())
        now = datetime.utcnow()

        self.analysis_collection.insert_one({
            "result_id": result_id,
            "project_id": project_id,
            "user_id": owner_id,
            "url": url if url else None,
            "project_dir": project_dir if project_dir else None,
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

        if process_semaphore._value > 0:
            asyncio.create_task(self._run_evaluation_with_semaphore(result_id, source, project_id, owner_id))
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

    async def _run_evaluation_with_semaphore(self, result_id, source, project_id, owner_id):
        async with process_semaphore:
            await self._run_evaluation_and_store(result_id, source, project_id, owner_id)

    async def _run_evaluation_and_store(self, result_id, source, project_id, owner_id):
        print("Evaluation started...")

        try:
            from core.evaluators.website_evaluator import WebsiteEvaluator
            from core.evaluators.project_evaluator import ProjectEvaluator
            from playwright.async_api import async_playwright
            import json
            import os
            from pathlib import Path

            def recursive_parse(data):
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

            if source.startswith("http://") or source.startswith("https://"):
                # Website evaluation
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        page = await browser.new_page()
                        await page.goto(source, timeout=60000)
                        html = await page.content()
                        body_text = await page.inner_text("body")

                        evaluator = WebsiteEvaluator(
                            root_url=source,
                            max_subpages=100,
                            max_depth=3,
                            concurrency=5,
                            custom_criteria={},
                            page=page
                        )

                        results = await evaluator.evaluate_page(html, body_text)
                        if asyncio.iscoroutine(results):
                            results = await results
                    finally:
                        await browser.close()
            else:
                # Local project folder evaluation
                if not os.path.isdir(source):
                    raise Exception(f"Project directory '{source}' does not exist.")

                evaluator = ProjectEvaluator(Path(source))
                results = await evaluator.evaluate()
                if asyncio.iscoroutine(results):
                    results = await results

            results = recursive_parse(results)

            update_data = {
                "status": "completed",
                "result": results,
                "analysis_date": datetime.utcnow()
            }

            self.analysis_collection.update_one(
                {"result_id": result_id},
                {"$set": update_data}
            )

            self.project_collection.update_one(
                {"project_id": project_id},
                {
                    "$push": {"analysis_result_ids": result_id},
                    "$set": {"last_updated": datetime.utcnow()}
                }
            )

            print(f"✅ Evaluation completed and saved for project: {project_id}")

        except Exception as e:
            print(f"❌ Error during evaluation: {e}")
            self.analysis_collection.update_one(
                {"result_id": result_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )
            self.project_collection.update_one(
                {"project_id": project_id},
                {
                    "$set": {"last_updated": datetime.utcnow()},
                    "$pull": {"analysis_result_ids": result_id}
                }
            )