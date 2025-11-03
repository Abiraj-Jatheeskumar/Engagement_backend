"""
Zoom API integration for fetching live participants
"""
import requests
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class ZoomAPI:
    """Zoom API client for fetching meeting participants"""
    
    def __init__(self):
        self.api_key = os.getenv("ZOOM_API_KEY")
        self.api_secret = os.getenv("ZOOM_API_SECRET")
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.base_url = "https://api.zoom.us/v2"
        self.access_token: Optional[str] = None
    
    def get_access_token(self) -> str:
        """
        Get OAuth access token for Zoom API
        
        Returns:
            Access token string
        """
        if self.access_token:
            return self.access_token
        
        url = f"https://zoom.us/oauth/token"
        
        headers = {
            "Authorization": f"Basic {self._get_basic_auth()}"
        }
        
        params = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }
        
        try:
            response = requests.post(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            logger.info("Successfully obtained Zoom access token")
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to get Zoom access token: {e}")
            raise
    
    def _get_basic_auth(self) -> str:
        """Get basic auth string for Zoom OAuth"""
        import base64
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    def get_meeting_participants(self, meeting_id: str) -> List[Dict]:
        """
        Get list of participants in a live meeting
        
        Args:
            meeting_id: Zoom meeting ID
        
        Returns:
            List of participant dictionaries
        """
        token = self.get_access_token()
        
        url = f"{self.base_url}/meetings/{meeting_id}/participants"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            participants = data.get("participants", [])
            logger.info(f"Retrieved {len(participants)} participants from meeting {meeting_id}")
            return participants
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Meeting {meeting_id} not found")
            else:
                logger.error(f"Failed to get meeting participants: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching meeting participants: {e}")
            return []
    
    def get_meeting_info(self, meeting_id: str) -> Optional[Dict]:
        """
        Get meeting information
        
        Args:
            meeting_id: Zoom meeting ID
        
        Returns:
            Meeting information dictionary
        """
        token = self.get_access_token()
        
        url = f"{self.base_url}/meetings/{meeting_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            meeting_info = response.json()
            return meeting_info
        except Exception as e:
            logger.error(f"Failed to get meeting info: {e}")
            return None

