"""
WebSocket endpoint for instructor dashboard
Sends real-time engagement updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from database.schema import DashboardUpdate, EngagementMessage
import json
import logging

logger = logging.getLogger(__name__)


class InstructorWebSocketManager:
    """Manage WebSocket connections for instructors"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}  # instructor_id -> set of websockets
        self.instructor_sessions: Dict[WebSocket, int] = {}  # websocket -> instructor_id
    
    async def connect(self, websocket: WebSocket, instructor_id: int):
        """
        Accept WebSocket connection from instructor
        
        Args:
            websocket: WebSocket connection
            instructor_id: Instructor ID
        """
        await websocket.accept()
        
        if instructor_id not in self.active_connections:
            self.active_connections[instructor_id] = set()
        
        self.active_connections[instructor_id].add(websocket)
        self.instructor_sessions[websocket] = instructor_id
        
        logger.info(f"Instructor {instructor_id} connected")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection
        
        Args:
            websocket: WebSocket connection
        """
        instructor_id = self.instructor_sessions.get(websocket)
        
        if instructor_id and instructor_id in self.active_connections:
            self.active_connections[instructor_id].remove(websocket)
            logger.info(f"Instructor {instructor_id} disconnected")
        
        if websocket in self.instructor_sessions:
            del self.instructor_sessions[websocket]
    
    async def send_dashboard_update(self, instructor_id: int, update: DashboardUpdate):
        """
        Send dashboard update to instructor
        
        Args:
            instructor_id: Instructor ID
            update: Dashboard update message
        """
        if instructor_id not in self.active_connections:
            return
        
        message = update.dict()
        
        for websocket in list(self.active_connections[instructor_id]):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending dashboard update to instructor {instructor_id}: {e}")
    
    async def send_engagement_update(self, instructor_id: int, update: EngagementMessage):
        """
        Send engagement update to instructor
        
        Args:
            instructor_id: Instructor ID
            update: Engagement message
        """
        if instructor_id not in self.active_connections:
            return
        
        message = update.dict()
        
        for websocket in list(self.active_connections[instructor_id]):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending engagement update to instructor {instructor_id}: {e}")


# Global WebSocket manager
_instructor_ws_manager = InstructorWebSocketManager()


def get_instructor_ws_manager() -> InstructorWebSocketManager:
    """Get the global instructor WebSocket manager"""
    return _instructor_ws_manager

