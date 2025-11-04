from fastapi import WebSocket
from typing import Dict, List
import json
from models import WebSocketMessage, Status, State

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        if user_id not in self.connections:
            self.connections[user_id] = []
        
        self.connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.connections:
            self.connections[user_id].remove(websocket)
            if not self.connections[user_id]:
                del self.connections[user_id]
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        if user_id in self.connections:
            message_json = message.json()
            disconnected = []
            
            for websocket in self.connections[user_id]:
                try:
                    await websocket.send_text(message_json)
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.connections[user_id].remove(ws)
            
            # Clean up empty user connections
            if not self.connections[user_id]:
                del self.connections[user_id]
    
    async def broadcast_status_update(self, user_id: str, measurement_id: str, status: Status):
        message = WebSocketMessage(
            type="status_update",
            measurement_id=measurement_id,
            status=status
        )
        await self.send_to_user(user_id, message)
    
    async def broadcast_state_update(self, user_id: str, measurement_id: str, state: State):
        message = WebSocketMessage(
            type="state_update",
            measurement_id=measurement_id,
            state=state
        )
        await self.send_to_user(user_id, message)
    
    async def broadcast_results_update(self, user_id: str, measurement_id: str, results: dict):
        print("TASK CREATED")
        message = WebSocketMessage(
            type="results_update",
            measurement_id=measurement_id,
            status=Status.done,
            results=results
        )
        await self.send_to_user(user_id, message)
    
    async def broadcast_error_update(self, user_id: str, measurement_id: str, errors: list):
        message = WebSocketMessage(
            type="error_update",
            measurement_id=measurement_id,
            status=Status.error,
            errors=errors
        )
        await self.send_to_user(user_id, message)

websocket_manager = WebSocketManager()
