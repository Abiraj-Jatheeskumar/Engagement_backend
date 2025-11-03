"""
API routes for Zoom integration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from zoom_integrator.zoom_api import ZoomAPI
from zoom_integrator.zoom_events import get_zoom_event_handler
from zoom_integrator.session_manager import get_session_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zoom", tags=["zoom"])
zoom_api = ZoomAPI()
zoom_handler = get_zoom_event_handler()
session_manager = get_session_manager()


@router.get("/meetings/{meeting_id}/participants")
async def get_meeting_participants(meeting_id: str):
    """
    Get current participants in a Zoom meeting
    
    Args:
        meeting_id: Zoom meeting ID
    
    Returns:
        List of participants
    """
    try:
        participants = zoom_api.get_meeting_participants(meeting_id)
        return {"meeting_id": meeting_id, "participants": participants, "count": len(participants)}
    except Exception as e:
        logger.error(f"Error fetching meeting participants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch meeting participants")


@router.get("/meetings/{meeting_id}/info")
async def get_meeting_info(meeting_id: str):
    """
    Get information about a Zoom meeting
    
    Args:
        meeting_id: Zoom meeting ID
    
    Returns:
        Meeting information
    """
    try:
        meeting_info = zoom_api.get_meeting_info(meeting_id)
        
        if not meeting_info:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return meeting_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meeting info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch meeting info")


@router.post("/session/{session_id}/sync-participants")
async def sync_session_participants(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Sync participants from Zoom meeting to session
    
    Args:
        session_id: Session ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        session_manager.update_session_students(db, session_id)
        return {"message": "Participants synchronized successfully"}
    except Exception as e:
        logger.error(f"Error syncing participants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync participants")

