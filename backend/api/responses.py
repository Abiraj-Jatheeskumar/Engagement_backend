"""
API routes for student responses
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database import models, schema
from database.schema import ResponseCreate, ResponseResponse
from services.engagement_service import EngagementService
from websocket.instructor_ws import get_instructor_ws_manager
from websocket.student_ws import get_student_ws_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/responses", tags=["responses"])
engagement_service = EngagementService()
instructor_ws = get_instructor_ws_manager()


@router.post("/", response_model=ResponseResponse)
async def submit_response(
    response: ResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a student response to a question
    
    Args:
        response: Response data
        db: Database session
    
    Returns:
        Created response
    """
    try:
        # Get question to verify answer
        question = db.query(models.Question).filter(models.Question.id == response.question_id).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Check if answer is correct (simple string comparison for now)
        is_correct = response.response_text.lower().strip() == question.correct_answer.lower().strip()
        
        # Create response record
        db_response = models.Response(
            student_id=response.student_id,
            question_id=response.question_id,
            session_id=response.session_id,
            response_text=response.response_text,
            response_time_ms=response.response_time_ms,
            is_correct=is_correct
        )
        
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        
        # Log engagement
        engagement_service.log_engagement(
            db,
            response.student_id,
            response.session_id,
            response.response_time_ms,
            is_correct
        )
        
        logger.info(f"Student {response.student_id} submitted response: correct={is_correct}")
        
        return db_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit response")


@router.get("/", response_model=List[ResponseResponse])
async def get_all_responses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all responses
    
    Args:
        skip: Number of responses to skip
        limit: Maximum number of responses to return
        db: Database session
    
    Returns:
        List of responses
    """
    responses = db.query(models.Response).offset(skip).limit(limit).all()
    return responses


@router.get("/session/{session_id}", response_model=List[ResponseResponse])
async def get_session_responses(
    session_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all responses for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of responses to return
        db: Database session
    
    Returns:
        List of responses
    """
    responses = (
        db.query(models.Response)
        .filter(models.Response.session_id == session_id)
        .order_by(models.Response.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return responses


@router.get("/student/{student_id}", response_model=List[ResponseResponse])
async def get_student_responses(
    student_id: int,
    session_id: int = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all responses for a student
    
    Args:
        student_id: Student ID
        session_id: Optional session ID to filter
        limit: Maximum number of responses to return
        db: Database session
    
    Returns:
        List of responses
    """
    query = db.query(models.Response).filter(models.Response.student_id == student_id)
    
    if session_id:
        query = query.filter(models.Response.session_id == session_id)
    
    responses = query.order_by(models.Response.timestamp.desc()).limit(limit).all()
    return responses

