from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from playwright.async_api import async_playwright
from core.analyzers.page_evaluator import PageEvaluator
from core.analyzers.report_generator import ReportGenerator
import logging
from typing import List

app = FastAPI()
logger = logging.getLogger(__name__)

class EvaluationRequest(BaseModel):
    url: str
    design_data: dict = {}

class BatchEvaluationRequest(BaseModel):
    urls: List[str]
    design_data: dict = {}

@app.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(request.url, timeout=60000)
            evaluator = PageEvaluator(request.url, page, request.design_data)
            report = await evaluator.evaluate()
            await page.close()
            await browser.close()
        return report
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.post("/evaluate/pdf")
async def evaluate_pdf(request: EvaluationRequest):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(request.url, timeout=60000)
            evaluator = PageEvaluator(request.url, page, request.design_data)
            report = await evaluator.evaluate()
            await page.close()
            await browser.close()
        pdf_bytes = ReportGenerator.generate_pdf(report)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.post("/evaluate/batch")
async def evaluate_batch(request: BatchEvaluationRequest):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for url in request.urls:
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=60000)
                evaluator = PageEvaluator(url, page, request.design_data)
                report = await evaluator.evaluate()
                results.append({"url": url, "report": report})
                await page.close()
            except Exception as e:
                logger.error(f"Batch evaluation failed for {url}: {str(e)}")
                results.append({"url": url, "error": str(e)})
        await browser.close()
    return results

@app.get("/trend")
async def trend():
    # Stub: no real DB, just return dummy trend
    return ReportGenerator.get_trend_analysis()

@app.get("/health")
async def health():
    return {"status": "ok"} 