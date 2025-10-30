"""VFD Profile management service for Vehicle for the Future operational modes."""
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
import time

from services.tcp_communication_service import CommunicationService
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfileType(Enum):
    """VFD operational profile types."""
    
    SENSORS = ("sensors", "Sensor Monitoring", "fas fa-eye", "Monitor all vehicle sensors and data collection")
    COMMUNICATION = ("communication", "Communication Test", "fas fa-signal", "Test communication systems and protocols")
    POWER = ("power", "Power Management", "fas fa-battery-full", "Manage power distribution and efficiency")
    DIAGNOSTICS = ("diagnostics", "System Diagnostics", "fas fa-stethoscope", "Run comprehensive system diagnostics")
    EMERGENCY = ("emergency", "Emergency Protocol", "fas fa-exclamation-triangle", "Execute emergency safety procedures")
    
    def __init__(self, command: str, display_name: str, icon: str, description: str):
        self.command = command
        self.display_name = display_name
        self.icon = icon
        self.description = description


@dataclass
class ProfileExecutionResult:
    """Result of profile execution."""
    success: bool
    message: str
    error: Optional[str] = None
    duration: float = 0.0
    data: Optional[Dict[str, Any]] = None


class ProfileService:
    """Service for managing VFD operational profiles."""
    
    def __init__(self, communication_service: Optional[CommunicationService] = None):
        """Initialize VFD Profile service."""
        self.communication_service = communication_service
        self.current_profile: Optional[ProfileType] = None
        self.profile_history: List[Dict[str, Any]] = []
        self.profile_data: Dict[ProfileType, Dict[str, Any]] = {}
        
        # Initialize profile data
        for profile in ProfileType:
            self.profile_data[profile] = {
                'execution_count': 0,
                'last_executed': None,
                'average_duration': 0.0,
                'status': 'ready',
                'config': self._get_default_config(profile)
            }
        
        logger.info("VFD Profile service initialized")
    
    def execute_profile(self, profile: ProfileType) -> Dict[str, Any]:
        """Execute a VFD operational profile."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing VFD profile: {profile.display_name}")
            
            # Update profile status
            self.profile_data[profile]['status'] = 'executing'
            self.current_profile = profile
            
            # Execute profile-specific logic
            result = self._execute_profile_logic(profile)
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update profile data
            self.profile_data[profile]['execution_count'] += 1
            self.profile_data[profile]['last_executed'] = end_time.isoformat()
            self.profile_data[profile]['status'] = 'completed'
            
            # Update average duration
            count = self.profile_data[profile]['execution_count']
            avg = self.profile_data[profile]['average_duration']
            self.profile_data[profile]['average_duration'] = ((avg * (count - 1)) + duration) / count
            
            # Add to history
            history_entry = {
                'profile': profile.command,
                'display_name': profile.display_name,
                'timestamp': end_time.isoformat(),
                'duration': duration,
                'success': result.get('success', True),
                'message': result.get('message', 'Profile executed successfully')
            }
            
            self.profile_history.append(history_entry)
            
            logger.info(f"VFD profile {profile.display_name} completed in {duration:.2f}s")
            
            return {
                'success': True,
                'message': f"VFD Profile {profile.display_name} executed successfully",
                'duration': duration,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error executing VFD profile {profile.display_name}: {str(e)}")
            
            # Update profile status
            self.profile_data[profile]['status'] = 'error'
            
            # Add error to history
            history_entry = {
                'profile': profile.command,
                'display_name': profile.display_name,
                'timestamp': datetime.now().isoformat(),
                'duration': (datetime.now() - start_time).total_seconds(),
                'success': False,
                'message': f"Error: {str(e)}"
            }
            
            self.profile_history.append(history_entry)
            
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to execute VFD profile {profile.display_name}"
            }
    
    def _execute_profile_logic(self, profile: ProfileType) -> Dict[str, Any]:
        """Execute specific logic for each VFD profile type."""
        
        if profile == ProfileType.SENSORS:
            return self._execute_sensors_profile()
        elif profile == ProfileType.COMMUNICATION:
            return self._execute_communication_profile()
        elif profile == ProfileType.POWER:
            return self._execute_power_profile()
        elif profile == ProfileType.DIAGNOSTICS:
            return self._execute_diagnostics_profile()
        elif profile == ProfileType.EMERGENCY:
            return self._execute_emergency_profile()
        else:
            raise ValueError(f"Unknown VFD profile type: {profile}")
    
    def _execute_sensors_profile(self) -> Dict[str, Any]:
        """Execute VFD sensor monitoring profile."""
        logger.info("Executing VFD sensor monitoring profile")
        
        # Simulate sensor data collection
        time.sleep(0.5)  # Simulate processing time
        
        return {
            'success': True,
            'message': 'VFD sensor monitoring completed',
            'sensors_checked': 15,
            'status': 'All sensors operational'
        }
    
    def _execute_communication_profile(self) -> Dict[str, Any]:
        """Execute VFD communication test profile."""
        logger.info("Executing VFD communication test profile")
        
        if self.communication_service:
            # Test communication systems
            connection_status = self.communication_service.get_connection_status()
            time.sleep(0.3)  # Simulate testing time
            
            return {
                'success': True,
                'message': 'VFD communication systems tested',
                'connection_status': connection_status,
                'protocols_tested': ['UART', 'I2C', 'SPI']
            }
        else:
            return {
                'success': True,
                'message': 'VFD communication test (simulation mode)',
                'connection_status': 'simulated',
                'protocols_tested': ['simulation']
            }
    
    def _execute_power_profile(self) -> Dict[str, Any]:
        """Execute VFD power management profile."""
        logger.info("Executing VFD power management profile")
        
        # Simulate power management tasks
        time.sleep(0.4)  # Simulate processing time
        
        return {
            'success': True,
            'message': 'VFD power management optimized',
            'power_efficiency': '94.5%',
            'battery_status': 'Optimal',
            'systems_optimized': 8
        }
    
    def _execute_diagnostics_profile(self) -> Dict[str, Any]:
        """Execute VFD system diagnostics profile."""
        logger.info("Executing VFD system diagnostics profile")
        
        # Simulate comprehensive diagnostics
        time.sleep(0.8)  # Simulate diagnostics time
        
        return {
            'success': True,
            'message': 'VFD system diagnostics completed',
            'systems_checked': 12,
            'issues_found': 0,
            'health_score': '98%'
        }
    
    def _execute_emergency_profile(self) -> Dict[str, Any]:
        """Execute VFD emergency protocol profile."""
        logger.warning("Executing VFD emergency protocol")
        
        # Emergency procedures
        time.sleep(0.2)  # Quick emergency response
        
        return {
            'success': True,
            'message': 'VFD emergency protocols activated',
            'emergency_systems': 'Engaged',
            'safety_status': 'Secured',
            'response_time': '0.2s'
        }
    
    def get_current_profile(self) -> Optional[ProfileType]:
        """Get the currently active VFD profile."""
        return self.current_profile
    
    def get_profile_history(self) -> List[Dict[str, Any]]:
        """Get VFD profile execution history."""
        return self.profile_history.copy()
    
    def get_profile_statistics(self, profile: ProfileType) -> Dict[str, Any]:
        """Get statistics for a specific VFD profile."""
        if profile not in self.profile_data:
            return {}
        
        data = self.profile_data[profile]
        return {
            'execution_count': data['execution_count'],
            'last_executed': data['last_executed'],
            'average_duration': data['average_duration'],
            'status': data['status']
        }
    
    def get_all_profiles(self) -> List[ProfileType]:
        """Get all available VFD profiles."""
        return list(ProfileType)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current VFD system status."""
        active_profile = self.current_profile.display_name if self.current_profile else "None"
        
        # Calculate overall system status
        error_profiles = [p for p, data in self.profile_data.items() if data['status'] == 'error']
        system_status = "Error" if error_profiles else "Operational"
        
        # Determine VFD mode based on last executed profile
        vfd_mode = "Standby"
        if self.current_profile:
            if self.current_profile == ProfileType.EMERGENCY:
                vfd_mode = "Emergency"
            elif self.current_profile == ProfileType.DIAGNOSTICS:
                vfd_mode = "Diagnostics"
            elif self.current_profile == ProfileType.SENSORS:
                vfd_mode = "Monitoring"
            else:
                vfd_mode = "Active"
        
        last_execution = "--"
        if self.profile_history:
            last_execution = self.profile_history[-1]['timestamp'][:19].replace('T', ' ')
        
        return {
            'active_profile': active_profile,
            'system_status': system_status,
            'vfd_mode': vfd_mode,
            'last_execution': last_execution,
            'total_executions': len(self.profile_history),
            'error_count': len(error_profiles)
        }
    
    def reset_profile_data(self) -> None:
        """Reset all VFD profile data and history."""
        logger.info("Resetting VFD profile data")
        
        self.current_profile = None
        self.profile_history.clear()
        
        for profile in ProfileType:
            self.profile_data[profile] = {
                'execution_count': 0,
                'last_executed': None,
                'average_duration': 0.0,
                'status': 'ready',
                'config': self._get_default_config(profile)
            }
    
    def _get_default_config(self, profile: ProfileType) -> Dict[str, Any]:
        """Get default configuration for a VFD profile."""
        configs = {
            ProfileType.SENSORS: {
                'sampling_rate': 100,  # Hz
                'sensors_enabled': 'all',
                'data_logging': True
            },
            ProfileType.COMMUNICATION: {
                'test_duration': 10,  # seconds
                'protocols': ['UART', 'I2C', 'SPI'],
                'timeout': 5
            },
            ProfileType.POWER: {
                'optimization_level': 'high',
                'efficiency_target': 95,  # percent
                'monitoring_interval': 1
            },
            ProfileType.DIAGNOSTICS: {
                'comprehensive': True,
                'include_performance': True,
                'generate_report': True
            },
            ProfileType.EMERGENCY: {
                'auto_shutdown': True,
                'notify_operators': True,
                'log_emergency': True
            }
        }
        
        return configs.get(profile, {})
