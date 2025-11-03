"""
API routes for engagement management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database import models, schema
from database.schema import EngagementLogResponse, EngagementUpdate
from services.engagement_service import EngagementService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engagement", tags=["engagement"])
engagement_service = EngagementService()


@router.post("/log", response_model=EngagementLogResponse)
async def log_engagement(
    student_id: int,
    session_id: int,
    response_time_ms: int,
    is_correct: bool,
    db: Session = Depends(get_db)
):
    """
    Log student engagement based on response
    
    Args:
        student_id: Student ID
        session_id: Session ID
        response_time_ms: Response time in milliseconds
        is_correct: Whether answer was correct
        db: Database session
    
    Returns:
        Created engagement log
    """
    try:
        engagement_log = engagement_service.log_engagement(
            db, student_id, session_id, response_time_ms, is_correct
        )
        return engagement_log
    except Exception as e:
        logger.error(f"Error logging engagement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log engagement")


@router.get("/session/{session_id}", response_model=List[EngagementLogResponse])
async def get_session_engagement_logs(
    session_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get engagement logs for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of logs to return
        db: Database session
    
    Returns:
        List of engagement logs
    """
    logs = (
        db.query(models.EngagementLog)
        .filter(models.EngagementLog.session_id == session_id)
        .order_by(models.EngagementLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return logs


@router.get("/session/{session_id}/stats")
async def get_session_engagement_stats(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get aggregated engagement statistics for a session
    
    Args:
        session_id: Session ID
        db: Database session
    
    Returns:
        Dictionary with engagement statistics
    """
    stats = engagement_service.get_session_engagement_stats(db, session_id)
    return stats


@router.get("/student/{student_id}/session/{session_id}", response_model=EngagementLogResponse)
async def get_student_current_engagement(
    student_id: int,
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current engagement level for a student
    
    Args:
        student_id: Student ID
        session_id: Session ID
        db: Database session
    
    Returns:
        Latest engagement log
    """
    log = (
        db.query(models.EngagementLog)
        .filter(models.EngagementLog.student_id == student_id)
        .filter(models.EngagementLog.session_id == session_id)
        .order_by(models.EngagementLog.timestamp.desc())
        .first()
    )
    
    if not log:
        raise HTTPException(status_code=404, detail="No engagement data found")
    
    return log


@router.get("/student/{student_id}/session/{session_id}/history", response_model=List[EngagementLogResponse])
async def get_student_engagement_history(
    student_id: int,
    session_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get engagement history for a student
    
    Args:
        student_id: Student ID
        session_id: Session ID
        limit: Maximum number of logs to return
        db: Database session
    
    Returns:
        List of engagement logs
    """
    history = engagement_service.get_student_engagement_history(
        db, student_id, session_id, limit
    )
    return history

