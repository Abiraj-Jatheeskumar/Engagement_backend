"""
API routes for session management
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database import models, schema
from database.schema import SessionResponse, SessionCreate, DashboardStats, StudentEngagementStatus
from zoom_integrator.session_manager import get_session_manager
from websocket.instructor_ws import get_instructor_ws_manager
from services.engagement_service import EngagementService
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
session_manager = get_session_manager()
engagement_service = EngagementService()
instructor_ws = get_instructor_ws_manager()


@router.post("/", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new session
    
    Args:
        session: Session data
        db: Database session
    
    Returns:
        Created session
    """
    db_session = session_manager.create_session(
        db, session.instructor_id, session.zoom_meeting_id
    )
    return db_session


@router.get("/", response_model=List[SessionResponse])
async def get_all_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all sessions
    
    Args:
        skip: Number of sessions to skip
        limit: Maximum number of sessions to return
        db: Database session
    
    Returns:
        List of sessions
    """
    sessions = db.query(models.Session).offset(skip).limit(limit).all()
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific session by ID
    
    Args:
        session_id: Session ID
        db: Database session
    
    Returns:
        Session details
    """
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.post("/{session_id}/start")
async def start_session(
    session_id: int,
    student_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Start a session
    
    Args:
        session_id: Session ID
        student_ids: List of student IDs
        db: Database session
    """
    try:
        session_manager.start_session(db, session_id, set(student_ids))
        return {"message": "Session started successfully"}
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/stop")
async def stop_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Stop a session
    
    Args:
        session_id: Session ID
        db: Database session
    """
    try:
        session_manager.stop_session(db, session_id)
        return {"message": "Session stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/dashboard")
async def get_session_dashboard(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get dashboard data for a session
    
    Args:
        session_id: Session ID
        db: Database session
    
    Returns:
        Dashboard data with stats and student engagement
    """
    # Get session
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get engagement stats
    stats = engagement_service.get_session_engagement_stats(db, session_id)
    
    # Get unique students in session
    student_responses = (
        db.query(models.Response.student_id, func.count(models.Response.id).label('response_count'))
        .filter(models.Response.session_id == session_id)
        .group_by(models.Response.student_id)
        .all()
    )
    
    # Build student engagement status list
    students = []
    for student_id, _ in student_responses:
        # Get latest engagement
        engagement_log = (
            db.query(models.EngagementLog)
            .filter(models.EngagementLog.student_id == student_id)
            .filter(models.EngagementLog.session_id == session_id)
            .order_by(models.EngagementLog.timestamp.desc())
            .first()
        )
        
        current_engagement = engagement_log.engagement_level if engagement_log else models.EngagementLevel.MODERATE
        
        # Get response stats
        responses = (
            db.query(models.Response)
            .filter(models.Response.student_id == student_id)
            .filter(models.Response.session_id == session_id)
            .all()
        )
        
        response_count = len(responses)
        correct_count = sum(1 for r in responses if r.is_correct)
        avg_response_time = sum(r.response_time_ms for r in responses) / response_count if response_count > 0 else 0
        
        # Get student info
        student = db.query(models.User).filter(models.User.id == student_id).first()
        
        students.append(StudentEngagementStatus(
            student_id=student_id,
            student_name=student.name if student else f"Student {student_id}",
            student_email=student.email if student else "",
            current_engagement=current_engagement,
            response_count=response_count,
            correct_count=correct_count,
            avg_response_time=avg_response_time
        ))
    
    return {
        "session": session,
        "stats": stats,
        "students": students
    }


@router.websocket("/{session_id}/ws")
async def session_websocket(
    websocket: WebSocket,
    session_id: int,
    instructor_id: int
):
    """
    WebSocket endpoint for real-time session updates
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID
        instructor_id: Instructor ID
    """
    await instructor_ws.connect(websocket, instructor_id)
    
    try:
        while True:
            # Keep connection alive and forward updates
            data = await websocket.receive_text()
            # Echo or process any client messages
    except WebSocketDisconnect:
        instructor_ws.disconnect(websocket)
        logger.info(f"Instructor {instructor_id} disconnected from session {session_id}")


@router.post("/{session_id}/update-students")
async def update_session_students(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Update student list for active session from Zoom
    
    Args:
        session_id: Session ID
        db: Database session
    """
    try:
        session_manager.update_session_students(db, session_id)
        return {"message": "Session students updated successfully"}
    except Exception as e:
        logger.error(f"Error updating session students: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

