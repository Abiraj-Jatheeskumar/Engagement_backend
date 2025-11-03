"""
Adaptive interaction engine for dynamic question delivery
Monitors student engagement and adjusts question frequency
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import Dict, Set, Callable, Optional
from database import models, schema
from .engagement_service import EngagementService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdaptiveEngine:
    """
    Adaptive interaction engine that monitors engagement and delivers questions
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.engagement_service = EngagementService()
        self.active_sessions: Dict[int, Set[int]] = {}  # session_id -> set of student_ids
        self.question_push_callback: Optional[Callable] = None
        self.db_session_factory: Optional[Callable] = None
        self._running = False
    
    def initialize(
        self,
        db_session_factory: Callable,
        question_push_callback: Callable
    ):
        """
        Initialize engine with dependencies
        
        Args:
            db_session_factory: Function to create database sessions
            question_push_callback: Function to call when pushing questions to students
                Signature: callback(session_id: int, student_ids: List[int]) -> None
        """
        self.db_session_factory = db_session_factory
        self.question_push_callback = question_push_callback
    
    def start(self):
        """Start the adaptive engine"""
        if self._running:
            logger.warning("Adaptive engine already running")
            return
        
        # Schedule engagement monitoring every 10 seconds
        self.scheduler.add_job(
            self._monitor_engagement,
            IntervalTrigger(seconds=10),
            id='monitor_engagement',
            replace_existing=True
        )
        
        self.scheduler.start()
        self._running = True
        logger.info("Adaptive interaction engine started")
    
    def stop(self):
        """Stop the adaptive engine"""
        if not self._running:
            return
        
        self.scheduler.shutdown()
        self._running = False
        logger.info("Adaptive interaction engine stopped")
    
    def add_session(self, session_id: int, student_ids: Set[int]):
        """
        Add a session to monitor
        
        Args:
            session_id: Session ID
            student_ids: Set of student IDs in session
        """
        self.active_sessions[session_id] = student_ids
        logger.info(f"Added session {session_id} with {len(student_ids)} students")
    
    def remove_session(self, session_id: int):
        """
        Remove a session from monitoring
        
        Args:
            session_id: Session ID
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Removed session {session_id}")
    
    def update_session_students(self, session_id: int, student_ids: Set[int]):
        """
        Update student list for a session
        
        Args:
            session_id: Session ID
            student_ids: Set of student IDs
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id] = student_ids
    
    async def _monitor_engagement(self):
        """
        Monitor engagement for all active sessions and trigger questions
        This runs every 10 seconds
        """
        if not self.db_session_factory or not self.question_push_callback:
            logger.error("Adaptive engine not properly initialized")
            return
        
        db = self.db_session_factory()
        
        try:
            for session_id, student_ids in list(self.active_sessions.items()):
                students_needing_questions = self._identify_students_needing_questions(
                    db, session_id, student_ids
                )
                
                if students_needing_questions:
                    logger.info(
                        f"Session {session_id}: {len(students_needing_questions)} students need questions"
                    )
                    await self.question_push_callback(session_id, students_needing_questions)
        except Exception as e:
            logger.error(f"Error in engagement monitoring: {e}", exc_info=True)
        finally:
            db.close()
    
    def _identify_students_needing_questions(
        self,
        db: Session,
        session_id: int,
        student_ids: Set[int]
    ) -> Set[int]:
        """
        Identify which students need questions based on engagement
        
        Args:
            db: Database session
            session_id: Session ID
            student_ids: Set of student IDs
        
        Returns:
            Set of student IDs that need questions
        """
        students_needing_questions = set()
        
        for student_id in student_ids:
            engagement = self.engagement_service.get_current_engagement(
                db, student_id, session_id
            )
            
            should_get_question = self._should_deliver_question(
                engagement, student_id, session_id
            )
            
            if should_get_question:
                students_needing_questions.add(student_id)
        
        return students_needing_questions
    
    def _should_deliver_question(
        self,
        engagement: Optional[models.EngagementLevel],
        student_id: int,
        session_id: int
    ) -> bool:
        """
        Determine if a student should receive a question based on engagement
        
        Logic:
        - PASSIVE students: high frequency (every monitoring cycle if eligible)
        - MODERATE students: medium frequency
        - ACTIVE students: low frequency
        - No engagement data: default to moderate frequency
        
        Args:
            engagement: Current engagement level
            student_id: Student ID
            session_id: Session ID
        
        Returns:
            True if student should receive question
        """
        # Check last question time for this student to implement frequency control
        # For now, simple logic based on engagement
        
        if engagement is None:
            # No engagement data yet, deliver initial question
            return True
        
        # Simple rules-based frequency control
        # In production, implement time-based throttling
        
        if engagement == models.EngagementLevel.PASSIVE:
            # Passives get questions more frequently
            return True  # Simplified: always deliver for passive
        elif engagement == models.EngagementLevel.MODERATE:
            # Moderates get medium frequency
            # TODO: Add time-based throttling (e.g., max once per 30 seconds)
            return True
        elif engagement == models.EngagementLevel.ACTIVE:
            # Actives get low frequency
            # TODO: Add time-based throttling (e.g., max once per 2 minutes)
            return False
        
        return False


# Global engine instance
_adaptive_engine = AdaptiveEngine()


def get_adaptive_engine() -> AdaptiveEngine:
    """Get the global adaptive engine instance"""
    return _adaptive_engine

