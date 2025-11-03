"""
Session management for Zoom-integrated sessions
Manages the lifecycle of learning sessions
"""
from sqlalchemy.orm import Session
from typing import Dict, Set, Optional
from database import models
from datetime import datetime
from .zoom_events import get_zoom_event_handler
from ..services.adaptive_engine import get_adaptive_engine
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage learning session lifecycles"""
    
    def __init__(self):
        self.zoom_handler = get_zoom_event_handler()
        self.adaptive_engine = get_adaptive_engine()
    
    def create_session(
        self,
        db: Session,
        instructor_id: int,
        zoom_meeting_id: Optional[str] = None
    ) -> models.Session:
        """
        Create a new learning session
        
        Args:
            db: Database session
            instructor_id: Instructor user ID
            zoom_meeting_id: Optional Zoom meeting ID
        
        Returns:
            Created Session model
        """
        session = models.Session(
            instructor_id=instructor_id,
            zoom_meeting_id=zoom_meeting_id,
            start_time=datetime.utcnow(),
            status=models.SessionStatus.PENDING
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created session {session.id} for instructor {instructor_id}")
        return session
    
    def start_session(
        self,
        db: Session,
        session_id: int,
        student_ids: Set[int]
    ):
        """
        Start a session and begin monitoring
        
        Args:
            db: Database session
            session_id: Session ID
            student_ids: Set of student IDs
        """
        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = models.SessionStatus.ACTIVE
        db.commit()
        
        # Add session to adaptive engine
        self.adaptive_engine.add_session(session_id, student_ids)
        
        # Start Zoom monitoring if meeting ID exists
        if session.zoom_meeting_id:
            self.zoom_handler.start_monitoring(session.zoom_meeting_id)
        
        logger.info(f"Started session {session_id} with {len(student_ids)} students")
    
    def stop_session(self, db: Session, session_id: int):
        """
        Stop a session
        
        Args:
            db: Database session
            session_id: Session ID
        """
        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = models.SessionStatus.ENDED
        session.end_time = datetime.utcnow()
        db.commit()
        
        # Remove session from adaptive engine
        self.adaptive_engine.remove_session(session_id)
        
        # Stop Zoom monitoring
        if session.zoom_meeting_id:
            self.zoom_handler.stop_monitoring(session.zoom_meeting_id)
        
        logger.info(f"Stopped session {session_id}")
    
    def update_session_students(self, db: Session, session_id: int):
        """
        Update student list for active session based on Zoom participants
        
        Args:
            db: Database session
            session_id: Session ID
        """
        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        
        if not session or not session.zoom_meeting_id:
            return
        
        # Get current participants from Zoom
        student_ids = self.zoom_handler.get_student_ids_from_participants(
            session.zoom_meeting_id
        )
        
        # Update adaptive engine
        self.adaptive_engine.update_session_students(session_id, student_ids)
        
        logger.info(f"Updated session {session_id} with {len(student_ids)} students")
    
    def get_session_state(self, db: Session, session_id: int) -> Dict:
        """
        Get current session state
        
        Args:
            db: Database session
            session_id: Session ID
        
        Returns:
            Session state dictionary
        """
        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        
        if not session:
            return {}
        
        # Get student IDs from adaptive engine
        student_ids = self.adaptive_engine.active_sessions.get(session_id, set())
        
        return {
            "session_id": session.id,
            "status": session.status.value,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "zoom_meeting_id": session.zoom_meeting_id,
            "num_students": len(student_ids),
            "student_ids": list(student_ids)
        }


# Global session manager
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager"""
    return _session_manager

