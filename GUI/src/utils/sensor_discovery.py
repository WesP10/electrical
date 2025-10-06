"""
Sensor Discovery Utility
Scans the workspace for available sensor types from .ino files and directories
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class SensorDiscovery:
    """Discovers available sensors from the electrical workspace"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Default to the electrical workspace root
            current_file = Path(__file__).resolve()
            gui_dir = current_file.parent.parent.parent  # Back to GUI root
            self.base_path = gui_dir.parent  # Back to electrical root
        else:
            self.base_path = Path(base_path)
        
        logger.info(f"SensorDiscovery initialized with base path: {self.base_path}")
    
    def discover_all_sensors(self) -> List[Dict[str, str]]:
        """
        Discover all available sensors from the workspace
        Returns list of sensor info dicts with name, type, and source
        """
        sensors = []
        
        # Scan depreciated/Sensors directory
        depreciated_sensors_path = self.base_path / "depreciated" / "Sensors"
        if depreciated_sensors_path.exists():
            sensors.extend(self._scan_depreciated_sensors(depreciated_sensors_path))
        
        # Scan archived_resources/Workshop directory  
        workshop_path = self.base_path / "archived_resources" / "Workshop"
        if workshop_path.exists():
            sensors.extend(self._scan_workshop_sensors(workshop_path))
        
        logger.info(f"Discovered {len(sensors)} sensors total")
        return sensors
    
    def _scan_depreciated_sensors(self, sensors_path: Path) -> List[Dict[str, str]]:
        """Scan depreciated/Sensors directory for sensor folders"""
        sensors = []
        
        for item in sensors_path.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                sensor_info = {
                    'name': item.name.lower(),
                    'type': self._infer_sensor_type(item.name),
                    'source': 'depreciated/Sensors',
                    'path': str(item),
                    'pins': self._get_default_pins(item.name.lower())
                }
                sensors.append(sensor_info)
                logger.debug(f"Found sensor: {sensor_info['name']} in {sensor_info['source']}")
        
        return sensors
    
    def _scan_workshop_sensors(self, workshop_path: Path) -> List[Dict[str, str]]:
        """Scan archived_resources/Workshop directory for sensor folders"""
        sensors = []
        
        for item in workshop_path.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                sensor_info = {
                    'name': item.name.lower(),
                    'type': self._infer_sensor_type(item.name),
                    'source': 'archived_resources/Workshop',
                    'path': str(item),
                    'pins': self._get_default_pins(item.name.lower())
                }
                sensors.append(sensor_info)
                logger.debug(f"Found sensor: {sensor_info['name']} in {sensor_info['source']}")
        
        return sensors
    
    def _infer_sensor_type(self, sensor_name: str) -> str:
        """Infer the type of sensor based on its name"""
        name_lower = sensor_name.lower()
        
        # Map sensor names to types
        type_mapping = {
            'accelerometer': 'motion',
            'pressure': 'environmental', 
            'thermistor': 'environmental',
            'ultrasonic': 'distance',
            'line_sensor': 'optical',
            'proximity_sensor': 'distance',
            'servo': 'actuator',
            'vibration': 'motion',
            'relay': 'control',
            'nrf24l01': 'communication',
            'transmitter-receiver': 'communication',
            'vn-100': 'navigation',
            'inductproxsensor': 'distance'
        }
        
        for key, sensor_type in type_mapping.items():
            if key in name_lower:
                return sensor_type
        
        return 'generic'
    
    def _get_default_pins(self, sensor_name: str) -> List[str]:
        """Get default pin assignments for different sensor types"""
        
        # Pin mapping based on typical usage patterns
        pin_mapping = {
            'accelerometer': ['A1', 'D2', 'D3'],  # I2C typically
            'pressure': ['A2'],  # Analog pressure sensor
            'thermistor': ['A0'],  # Analog temperature
            'ultrasonic': ['D7', 'D8'],  # Trigger and echo pins
            'line_sensor': ['A0'],  # Analog line detection
            'proximity_sensor': ['A0'],  # Analog proximity
            'servo': ['D9'],  # PWM pin
            'vibration': ['D2'],  # Digital interrupt
            'relay': ['D4'],  # Digital control
            'nrf24l01': ['D10', 'D9', 'D2'],  # SPI pins
            'transmitter-receiver': ['D0', 'D1'],  # Serial pins
            'vn-100': ['D0', 'D1'],  # Serial communication
            'inductproxsensor': ['A3'],  # Analog inductive sensor
            'sensor': ['A0']  # Generic analog
        }
        
        for key, pins in pin_mapping.items():
            if key in sensor_name:
                return pins
        
        return ['A0']  # Default to analog pin
    
    def get_sensor_names(self) -> List[str]:
        """Get just the sensor names for quick access"""
        sensors = self.discover_all_sensors()
        return [sensor['name'] for sensor in sensors]

# Convenience function for quick access
def discover_workspace_sensors(base_path: str = None) -> List[str]:
    """Quick function to get list of sensor names from workspace"""
    discovery = SensorDiscovery(base_path)
    return discovery.get_sensor_names()