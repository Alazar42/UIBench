from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime

from ..evaluators.website_evaluator import WebsiteEvaluator
from ..models.evaluation import EvaluationRequest, EnhancedEvaluationReport
from ..utils.error_handler import handle_evaluation_error

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/evaluate", response_model=EnhancedEvaluationReport)
async def evaluate_website(request: EvaluationRequest):
    """
    Evaluate a website and return comprehensive analysis results.
    
    Args:
        request: EvaluationRequest containing URL and evaluation parameters
        
    Returns:
        EnhancedEvaluationReport with detailed analysis results
        
    Raises:
        HTTPException: If evaluation fails or invalid parameters provided
    """
    try:
        evaluator = WebsiteEvaluator(
            root_url=request.url,
            max_subpages=request.max_subpages,
            max_depth=request.max_depth,
            custom_criteria=request.custom_criteria
        )
        report = await evaluator.evaluate(crawl=request.crawl_subpages)
        return EnhancedEvaluationReport(**report)
    except Exception as e:
        error_detail = handle_evaluation_error(e)
        logger.error(f"Evaluation failed: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@router.websocket("/ws/evaluate")
async def websocket_evaluation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time website evaluation.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        JSON response with evaluation results
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            request = EvaluationRequest(**request_data)
            
            evaluator = WebsiteEvaluator(
                root_url=request.url,
                max_subpages=request.max_subpages,
                max_depth=request.max_depth,
                custom_criteria=request.custom_criteria
            )
            report = await evaluator.evaluate(crawl=request.crawl_subpages)
            await websocket.send_text(json.dumps(report))
    except Exception as e:
        error_detail = handle_evaluation_error(e)
        logger.error(f"WebSocket evaluation failed: {error_detail}")
        await websocket.close()

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API status.
    
    Returns:
        Dict with API status information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    } 