"""
Video meeting provider integrations for DMeeet platform.
Supports Daily.co, Zoom, Agora, and Jitsi Meet.
"""

import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from abc import ABC, abstractmethod


class MeetingProvider(ABC):
    """Abstract base class for meeting providers"""
    
    @abstractmethod
    def create_meeting(self, meeting_obj):
        """Create a meeting room with the provider"""
        pass
    
    @abstractmethod
    def get_meeting_info(self, meeting_id):
        """Get meeting information from provider"""
        pass
    
    @abstractmethod
    def delete_meeting(self, meeting_id):
        """Delete meeting from provider"""
        pass


class DailyProvider(MeetingProvider):
    """Daily.co meeting provider"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'DAILY_API_KEY', None)
        self.base_url = 'https://api.daily.co/v1'
    
    def create_meeting(self, meeting_obj):
        """Create a Daily.co meeting room"""
        if not self.api_key:
            # Return a basic Jitsi-style URL as fallback
            room_name = f"dmeet-{meeting_obj.room_id}"
            return {
                'meeting_url': f"https://meet.jit.si/{room_name}",
                'meeting_id': room_name,
                'password': meeting_obj.meeting_password
            }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'name': f"DMeeet-{meeting_obj.room_id}",
            'properties': {
                'start_time': int(meeting_obj.scheduled_start.timestamp()),
                'exp': int(meeting_obj.scheduled_end.timestamp()),
                'max_participants': meeting_obj.max_participants,
                'enable_chat': True,
                'enable_recording': True,
                'meeting_join_hook': True,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rooms",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                room_data = response.json()
                return {
                    'meeting_url': room_data['url'],
                    'meeting_id': room_data['name'],
                    'password': meeting_obj.meeting_password
                }
            else:
                # Fallback to Jitsi
                room_name = f"dmeet-{meeting_obj.room_id}"
                return {
                    'meeting_url': f"https://meet.jit.si/{room_name}",
                    'meeting_id': room_name,
                    'password': meeting_obj.meeting_password
                }
        except Exception:
            # Fallback to Jitsi
            room_name = f"dmeet-{meeting_obj.room_id}"
            return {
                'meeting_url': f"https://meet.jit.si/{room_name}",
                'meeting_id': room_name,
                'password': meeting_obj.meeting_password
            }
    
    def get_meeting_info(self, meeting_id):
        """Get meeting information from Daily.co"""
        if not self.api_key:
            return {}
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/rooms/{meeting_id}",
                headers=headers
            )
            return response.json() if response.status_code == 200 else {}
        except Exception:
            return {}
    
    def delete_meeting(self, meeting_id):
        """Delete meeting from Daily.co"""
        if not self.api_key:
            return True
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
        }
        
        try:
            response = requests.delete(
                f"{self.base_url}/rooms/{meeting_id}",
                headers=headers
            )
            return response.status_code == 200
        except Exception:
            return False


class ZoomProvider(MeetingProvider):
    """Zoom meeting provider"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'ZOOM_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'ZOOM_CLIENT_SECRET', None)
        self.base_url = 'https://api.zoom.us/v2'
    
    def create_meeting(self, meeting_obj):
        """Create a Zoom meeting"""
        # For now, fallback to Jitsi since Zoom requires OAuth setup
        room_name = f"dmeet-{meeting_obj.room_id}"
        return {
            'meeting_url': f"https://meet.jit.si/{room_name}",
            'meeting_id': room_name,
            'password': meeting_obj.meeting_password
        }
    
    def get_meeting_info(self, meeting_id):
        """Get meeting info from Zoom"""
        return {}
    
    def delete_meeting(self, meeting_id):
        """Delete meeting from Zoom"""
        return True


class AgoraProvider(MeetingProvider):
    """Agora meeting provider"""
    
    def __init__(self):
        self.app_id = getattr(settings, 'AGORA_APP_ID', None)
        self.app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
    
    def create_meeting(self, meeting_obj):
        """Create an Agora meeting"""
        # For now, fallback to Jitsi since Agora requires complex token generation
        room_name = f"dmeet-{meeting_obj.room_id}"
        return {
            'meeting_url': f"https://meet.jit.si/{room_name}",
            'meeting_id': room_name,
            'password': meeting_obj.meeting_password
        }
    
    def get_meeting_info(self, meeting_id):
        """Get meeting info from Agora"""
        return {}
    
    def delete_meeting(self, meeting_id):
        """Delete meeting from Agora"""
        return True


class JitsiProvider(MeetingProvider):
    """Jitsi Meet provider"""
    
    def create_meeting(self, meeting_obj):
        """Create a Jitsi meeting"""
        room_name = f"dmeet-{meeting_obj.room_id}"
        return {
            'meeting_url': f"https://meet.jit.si/{room_name}",
            'meeting_id': room_name,
            'password': meeting_obj.meeting_password
        }
    
    def get_meeting_info(self, meeting_id):
        """Get meeting info from Jitsi"""
        return {}
    
    def delete_meeting(self, meeting_id):
        """Delete meeting from Jitsi"""
        return True


def get_meeting_provider(provider_name):
    """Get meeting provider instance"""
    providers = {
        'daily': DailyProvider,
        'zoom': ZoomProvider,
        'agora': AgoraProvider,
        'jitsi': JitsiProvider,
    }
    
    provider_class = providers.get(provider_name, JitsiProvider)
    return provider_class()