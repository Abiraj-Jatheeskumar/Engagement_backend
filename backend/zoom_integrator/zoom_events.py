"""
Zoom event handling and participant management
"""
from typing import Dict, List, Set, Optional
from .zoom_api import ZoomAPI
import logging
import asyncio

logger = logging.getLogger(__name__)


class ZoomEventHandler:
    """Handle Zoom meeting events and maintain participant state"""
    
    def __init__(self):
        self.zoom_api = ZoomAPI()
        self.active_participants: Dict[str, Set[str]] = {}  # meeting_id -> set of user_names
        self.student_mapping: Dict[str, int] = {}  # zoom_username -> student_id
        self._running = False
    
    def set_student_mapping(self, mapping: Dict[str, int]):
        """
        Set mapping from Zoom usernames to student IDs
        
        Args:
            mapping: Dictionary mapping zoom_username -> student_id
        """
        self.student_mapping = mapping
        logger.info(f"Set student mapping for {len(mapping)} students")
    
    def start_monitoring(self, meeting_id: str):
        """
        Start monitoring a Zoom meeting
        
        Args:
            meeting_id: Zoom meeting ID
        """
        self.active_participants[meeting_id] = set()
        logger.info(f"Started monitoring meeting {meeting_id}")
    
    def stop_monitoring(self, meeting_id: str):
        """
        Stop monitoring a Zoom meeting
        
        Args:
            meeting_id: Zoom meeting ID
        """
        if meeting_id in self.active_participants:
            del self.active_participants[meeting_id]
        logger.info(f"Stopped monitoring meeting {meeting_id}")
    
    def get_participants(self, meeting_id: str) -> List[Dict]:
        """
        Get current participants in a meeting
        
        Args:
            meeting_id: Zoom meeting ID
        
        Returns:
            List of participant dictionaries with zoom username
        """
        participants = self.zoom_api.get_meeting_participants(meeting_id)
        
        # Extract usernames
        participant_list = []
        current_usernames = set()
        
        for participant in participants:
            username = participant.get("user_name", "")
            current_usernames.add(username)
            
            participant_dict = {
                "zoom_username": username,
                "email": participant.get("email", ""),
                "join_time": participant.get("join_time", "")
            }
            
            # Map to student ID if available
            if username in self.student_mapping:
                participant_dict["student_id"] = self.student_mapping[username]
            
            participant_list.append(participant_dict)
        
        # Update active participants
        if meeting_id in self.active_participants:
            self.active_participants[meeting_id] = current_usernames
        
        return participant_list
    
    def get_student_ids_from_participants(self, meeting_id: str) -> Set[int]:
        """
        Get student IDs from current meeting participants
        
        Args:
            meeting_id: Zoom meeting ID
        
        Returns:
            Set of student IDs
        """
        participants = self.get_participants(meeting_id)
        student_ids = set()
        
        for participant in participants:
            if "student_id" in participant:
                student_ids.add(participant["student_id"])
        
        return student_ids
    
    async def monitor_participants_async(
        self,
        meeting_id: str,
        callback: callable,
        interval_seconds: int = 30
    ):
        """
        Asynchronously monitor participants and call callback on changes
        
        Args:
            meeting_id: Zoom meeting ID
            callback: Async function to call with participant updates
            interval_seconds: Polling interval
        """
        self._running = True
        
        while self._running and meeting_id in self.active_participants:
            try:
                participants = self.get_participants(meeting_id)
                await callback(meeting_id, participants)
            except Exception as e:
                logger.error(f"Error in participant monitoring: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring_all(self):
        """Stop all monitoring"""
        self._running = False
        self.active_participants.clear()


# Global event handler
_zoom_event_handler = ZoomEventHandler()


def get_zoom_event_handler() -> ZoomEventHandler:
    """Get the global Zoom event handler"""
    return _zoom_event_handler

