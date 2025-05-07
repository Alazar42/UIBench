from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.services.websocket_service import WebSocketManager
from core.services.live_evaluation_service import LiveEvaluationService
import uuid

router = APIRouter()
websocket_manager = WebSocketManager()

class ProjectEvaluationRequest(BaseModel):
    project_root: str
    custom_criteria: Optional[dict] = None

@router.post("/start-evaluation")
async def start_evaluation(request: ProjectEvaluationRequest):
    """Start evaluation of a local project."""
    try:
        project_id = str(uuid.uuid4())
        service = LiveEvaluationService(request.project_root)
        await service.start()
        return {
            "project_id": project_id,
            "status": "evaluation_started",
            "message": "Project evaluation started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time evaluation updates."""
    await websocket_manager.connect(websocket, project_id)
    try:
        while True:
            message = await websocket.receive_text()
            await websocket_manager.handle_message(websocket, project_id, message)
    except Exception:
        websocket_manager.disconnect(websocket, project_id)

@router.get("/project-structure/{project_id}")
async def get_project_structure(project_id: str):
    """Get the structure of a project being evaluated."""
    if project_id not in websocket_manager.evaluation_services:
        raise HTTPException(status_code=404, detail="Project not found")
    
    service = websocket_manager.evaluation_services[project_id]
    return service.get_project_structure()

@router.get("/evaluation-results/{project_id}")
async def get_evaluation_results(project_id: str):
    """Get the current evaluation results for a project."""
    if project_id not in websocket_manager.evaluation_services:
        raise HTTPException(status_code=404, detail="Project not found")
    
    service = websocket_manager.evaluation_services[project_id]
    return service.get_evaluation_results()

@router.get("/file-analysis/{project_id}")
async def get_file_analysis(project_id: str, file_path: str):
    """Get analysis for a specific file in the project."""
    if project_id not in websocket_manager.evaluation_services:
        raise HTTPException(status_code=404, detail="Project not found")
    
    service = websocket_manager.evaluation_services[project_id]
    analysis = service.get_file_analysis(file_path)
    if analysis is None:
        raise HTTPException(status_code=404, detail="File not found or not supported")
    return analysis 