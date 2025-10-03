"""Profile service for managing system profiles."""
from typing import Dict, Optional, List
from enum import Enum

import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger
from core.exceptions import HyperloopGUIError
from services.communication_service import CommunicationService

logger = get_logger(__name__)


class ProfileType(Enum):
    """Enumeration of available system profiles."""
    PRE_ACCELERATION = ("1", "Pre Acceleration", "primary")
    ACCELERATION = ("2", "Acceleration", "primary")
    CRUISE = ("3", "Cruise", "success")
    DECELERATION = ("4", "Deceleration", "warning")
    CRAWL = ("5", "Crawl", "warning")
    STOP = ("6", "Stop", "warning")
    EMERGENCY = ("7", "Emergency", "danger")
    
    def __init__(self, command: str, label: str, color: str):
        self.command = command
        self.label = label
        self.color = color


class ProfileService:
    """Service for managing system profiles and state transitions."""
    
    def __init__(self, communication_service: CommunicationService):
        self.communication_service = communication_service
        self._current_profile: Optional[ProfileType] = None
        self._profile_history: List[ProfileType] = []
        logger.info("Profile service initialized")
    
    def switch_profile(self, profile: ProfileType) -> bool:
        """Switch to a specific profile."""
        try:
            # Send command to communication service
            success = self.communication_service.send_command(profile.command)
            
            if success:
                # Update current profile and history
                if self._current_profile:
                    self._profile_history.append(self._current_profile)
                self._current_profile = profile
                logger.info(f"Switched to profile: {profile.label}")
                return True
            else:
                logger.error(f"Failed to switch to profile: {profile.label}")
                return False
                
        except Exception as e:
            logger.error(f"Error switching to profile {profile.label}: {e}")
            return False
    
    def get_current_profile(self) -> Optional[ProfileType]:
        """Get the current active profile."""
        return self._current_profile
    
    def get_profile_history(self) -> List[ProfileType]:
        """Get the history of profile switches."""
        return self._profile_history.copy()
    
    def get_available_profiles(self) -> List[ProfileType]:
        """Get all available profiles."""
        return list(ProfileType)
    
    def emergency_stop(self) -> bool:
        """Immediately switch to emergency profile."""
        logger.warning("Emergency stop initiated!")
        return self.switch_profile(ProfileType.EMERGENCY)
    
    def can_switch_to(self, target_profile: ProfileType) -> bool:
        """Check if switching to target profile is allowed from current state."""
        # Basic state transition logic - can be expanded
        if not self._current_profile:
            # Can switch to any profile from initial state
            return True
        
        # Emergency can always be activated
        if target_profile == ProfileType.EMERGENCY:
            return True
        
        # Can't switch from emergency without going through stop first
        if self._current_profile == ProfileType.EMERGENCY and target_profile != ProfileType.STOP:
            return False
        
        # Add more sophisticated state transition rules here
        return True
    
    def get_profile_by_command(self, command: str) -> Optional[ProfileType]:
        """Get profile by command string."""
        for profile in ProfileType:
            if profile.command == command:
                return profile
        return None
    
    def reset(self) -> None:
        """Reset profile service to initial state."""
        self._current_profile = None
        self._profile_history.clear()
        logger.info("Profile service reset")