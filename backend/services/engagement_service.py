"""
Engagement service for tracking and updating student engagement
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from database import models, schema
from engagement_classifier.classifier import create_classifier
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EngagementService:
    """Service for managing student engagement"""
    
    def __init__(self):
        self.classifier = create_classifier(use_ml=False)
    
    def classify_engagement(
        self,
        response_time_ms: int,
        is_correct: bool
    ) -> models.EngagementLevel:
        """
        Classify student engagement from response data
        
        Args:
            response_time_ms: Response time in milliseconds
            is_correct: Whether answer was correct
        
        Returns:
            EngagementLevel
        """
        return self.classifier.classify(response_time_ms, is_correct)
    
    def log_engagement(
        self,
        db: Session,
        student_id: int,
        session_id: int,
        response_time_ms: int,
        is_correct: bool
    ) -> models.EngagementLog:
        """
        Log engagement level for a student
        
        Args:
            db: Database session
            student_id: Student ID
            session_id: Session ID
            response_time_ms: Response time
            is_correct: Correctness
        
        Returns:
            EngagementLog
        """
        # Classify engagement
        engagement_level = self.classify_engagement(response_time_ms, is_correct)
        
        # Create engagement log
        engagement_log = models.EngagementLog(
            student_id=student_id,
            session_id=session_id,
            engagement_level=engagement_level,
            timestamp=datetime.utcnow()
        )
        
        db.add(engagement_log)
        db.commit()
        db.refresh(engagement_log)
        
        logger.info(f"Logged engagement: student={student_id}, level={engagement_level}")
        return engagement_log
    
    def get_current_engagement(
        self,
        db: Session,
        student_id: int,
        session_id: int
    ) -> Optional[models.EngagementLevel]:
        """
        Get current engagement level for a student
        
        Args:
            db: Database session
            student_id: Student ID
            session_id: Session ID
        
        Returns:
            Current engagement level or None
        """
        log = (
            db.query(models.EngagementLog)
            .filter(models.EngagementLog.student_id == student_id)
            .filter(models.EngagementLog.session_id == session_id)
            .order_by(models.EngagementLog.timestamp.desc())
            .first()
        )
        
        return log.engagement_level if log else None
    
    def get_student_engagement_history(
        self,
        db: Session,
        student_id: int,
        session_id: int,
        limit: int = 10
    ) -> List[models.EngagementLog]:
        """
        Get engagement history for a student
        
        Args:
            db: Database session
            student_id: Student ID
            session_id: Session ID
            limit: Number of recent logs to return
        
        Returns:
            List of engagement logs
        """
        logs = (
            db.query(models.EngagementLog)
            .filter(models.EngagementLog.student_id == student_id)
            .filter(models.EngagementLog.session_id == session_id)
            .order_by(models.EngagementLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        
        return logs
    
    def get_session_engagement_stats(
        self,
        db: Session,
        session_id: int
    ) -> Dict:
        """
        Get aggregated engagement statistics for a session
        
        Args:
            db: Database session
            session_id: Session ID
        
        Returns:
            Dictionary with engagement statistics
        """
        # Get all engagement logs for session
        logs = (
            db.query(models.EngagementLog)
            .filter(models.EngagementLog.session_id == session_id)
            .all()
        )
        
        # Get unique students
        student_ids = list(set(log.student_id for log in logs))
        
        # Get latest engagement for each student
        student_engagement = {}
        for student_id in student_ids:
            latest_log = (
                db.query(models.EngagementLog)
                .filter(models.EngagementLog.student_id == student_id)
                .filter(models.EngagementLog.session_id == session_id)
                .order_by(models.EngagementLog.timestamp.desc())
                .first()
            )
            if latest_log:
                student_engagement[student_id] = latest_log.engagement_level
        
        # Calculate statistics
        stats = {
            'total_students': len(student_engagement),
            'active_students': sum(1 for e in student_engagement.values() if e == models.EngagementLevel.ACTIVE),
            'moderate_students': sum(1 for e in student_engagement.values() if e == models.EngagementLevel.MODERATE),
            'passive_students': sum(1 for e in student_engagement.values() if e == models.EngagementLevel.PASSIVE)
        }
        
        return stats

