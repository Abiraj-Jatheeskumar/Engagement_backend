"""
WebSocket endpoint for student interface
Handles incoming questions and outgoing responses
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from database.schema import QuestionMessage, ResponseMessage
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StudentWebSocketManager:
    """Manage WebSocket connections for students"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}  # session_id -> set of websockets
        self.student_sessions: Dict[WebSocket, int] = {}  # websocket -> student_id
    
    async def connect(self, websocket: WebSocket, session_id: int, student_id: int):
        """
        Accept WebSocket connection from student
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
            student_id: Student ID
        """
        await websocket.accept()
        
        # Add to active connections
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.student_sessions[websocket] = student_id
        
        logger.info(f"Student {student_id} connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection
        
        Args:
            websocket: WebSocket connection
        """
        student_id = self.student_sessions.get(websocket)
        
        # Find and remove from active connections
        for session_id, connections in list(self.active_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                logger.info(f"Student {student_id} disconnected from session {session_id}")
                break
        
        # Remove from student sessions
        if websocket in self.student_sessions:
            del self.student_sessions[websocket]
    
    async def send_question_to_student(self, session_id: int, student_id: int, question: QuestionMessage):
        """
        Send question to specific student via WebSocket
        
        Args:
            session_id: Session ID
            student_id: Student ID
            question: Question message
        """
        if session_id not in self.active_connections:
            logger.warning(f"No active connections for session {session_id}")
            return
        
        # Find WebSocket for this student
        target_websocket = None
        for ws, sid in self.student_sessions.items():
            if sid == student_id and ws in self.active_connections[session_id]:
                target_websocket = ws
                break
        
        if target_websocket:
            try:
                message = question.dict()
                await target_websocket.send_json(message)
                logger.info(f"Sent question to student {student_id}")
            except Exception as e:
                logger.error(f"Error sending question to student {student_id}: {e}")
        else:
            logger.warning(f"Student {student_id} not connected in session {session_id}")
    
    async def send_question_to_multiple_students(
        self,
        session_id: int,
        student_ids: Set[int],
        question: QuestionMessage
    ):
        """
        Send question to multiple students
        
        Args:
            session_id: Session ID
            student_ids: Set of student IDs
            question: Question message
        """
        for student_id in student_ids:
            await self.send_question_to_student(session_id, student_id, question)
    
    async def receive_response(self, websocket: WebSocket) -> ResponseMessage:
        """
        Receive response from student via WebSocket
        
        Args:
            websocket: WebSocket connection
        
        Returns:
            ResponseMessage
        """
        try:
            data = await websocket.receive_json()
            response = ResponseMessage(**data)
            return response
        except Exception as e:
            logger.error(f"Error receiving response: {e}")
            raise
    
    def get_connected_students(self, session_id: int) -> Set[int]:
        """
        Get set of connected student IDs for a session
        
        Args:
            session_id: Session ID
        
        Returns:
            Set of student IDs
        """
        if session_id not in self.active_connections:
            return set()
        
        connected_students = set()
        for ws in self.active_connections[session_id]:
            if ws in self.student_sessions:
                connected_students.add(self.student_sessions[ws])
        
        return connected_students


# Global WebSocket manager
_student_ws_manager = StudentWebSocketManager()


def get_student_ws_manager() -> StudentWebSocketManager:
    """Get the global student WebSocket manager"""
    return _student_ws_manager

