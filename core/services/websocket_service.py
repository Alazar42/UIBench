from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from .live_evaluation_service import LiveEvaluationService

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.evaluation_services: Dict[str, LiveEvaluationService] = {}
        
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
                if project_id in self.evaluation_services:
                    self.evaluation_services[project_id].stop()
                    del self.evaluation_services[project_id]
                    
    async def start_evaluation(self, project_id: str, project_root: str):
        """Start live evaluation for a project."""
        if project_id not in self.evaluation_services:
            service = LiveEvaluationService(project_root)
            self.evaluation_services[project_id] = service
            await service.start()
            
            # Start sending updates
            asyncio.create_task(self._send_updates(project_id))
            
    async def _send_updates(self, project_id: str):
        """Send periodic updates to connected clients."""
        while project_id in self.evaluation_services:
            service = self.evaluation_services[project_id]
            results = service.get_evaluation_results()
            structure = service.get_project_structure()
            
            update = {
                'type': 'evaluation_update',
                'data': {
                    'results': results,
                    'structure': structure
                }
            }
            
            await self.broadcast(project_id, json.dumps(update))
            await asyncio.sleep(1)  # Adjust update frequency as needed
            
    async def broadcast(self, project_id: str, message: str):
        """Broadcast a message to all connected clients for a project."""
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Handle disconnected clients
                    self.disconnect(connection, project_id)
                    
    async def handle_message(self, websocket: WebSocket, project_id: str, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'start_evaluation':
                project_root = data.get('project_root')
                if project_root:
                    await self.start_evaluation(project_id, project_root)
                    
            elif message_type == 'get_file_analysis':
                file_path = data.get('file_path')
                if file_path and project_id in self.evaluation_services:
                    service = self.evaluation_services[project_id]
                    analysis = service.get_file_analysis(file_path)
                    response = {
                        'type': 'file_analysis',
                        'data': analysis
                    }
                    await websocket.send_text(json.dumps(response))
                    
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON message'
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                'type': 'error',
                'message': str(e)
            })) 