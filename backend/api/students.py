"""
API routes for student interface
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database import models, schema
from database.schema import UserResponse, UserCreate, QuestionMessage, ResponseCreate, ResponseMessage
from websocket.student_ws import get_student_ws_manager
from services.engagement_service import EngagementService
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/students", tags=["students"])
student_ws = get_student_ws_manager()
engagement_service = EngagementService()


@router.post("/", response_model=UserResponse)
async def create_student(
    student: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create or get a student
    
    Args:
        student: Student data
        db: Database session
    
    Returns:
        Student user
    """
    # Check if student already exists
    existing = db.query(models.User).filter(
        models.User.student_id == student.student_id
    ).first()
    
    if existing:
        return existing
    
    # Create new student
    db_student = models.User(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    logger.info(f"Created student {db_student.id}")
    return db_student


@router.get("/{student_id}", response_model=UserResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    """
    Get student by ID
    
    Args:
        student_id: Student ID
        db: Database session
    
    Returns:
        Student details
    """
    student = db.query(models.User).filter(models.User.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student


@router.websocket("/{student_id}/session/{session_id}/ws")
async def student_websocket(
    websocket: WebSocket,
    student_id: int,
    session_id: int
):
    """
    WebSocket endpoint for student interface
    
    Args:
        websocket: WebSocket connection
        student_id: Student ID
        session_id: Session ID
    """
    await student_ws.connect(websocket, session_id, student_id)
    
    try:
        while True:
            # Receive response from student
            data = await websocket.receive_json()
            
            # Handle response submission
            if data.get("type") == "response":
                response_data = data
                logger.info(f"Received response from student {student_id}: {response_data}")
                # Response will be processed by the question push service
    except WebSocketDisconnect:
        student_ws.disconnect(websocket)
        logger.info(f"Student {student_id} disconnected from session {session_id}")

