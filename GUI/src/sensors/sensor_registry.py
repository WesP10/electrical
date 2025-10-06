"""
Sensor Registry - Hardcoded loading of all valid sensor class files
"""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Type, Any
import logging

logger = logging.getLogger(__name__)

class SensorRegistry:
    """Registry for all available sensor classes"""
    
    def __init__(self):
        self.sensor_classes: Dict[str, Type] = {}
        self._load_all_sensors()
    
    def _load_all_sensors(self):
        """Hardcode load all valid sensor.py files"""
        # List of all valid sensor files (without .py extension)
        sensor_files = [
            'ultrasonic_sensor',
            'accelerometer_sensor', 
            'pressure_sensor',
            'temperature_sensor',
            'thermistor_sensor',
            'line_sensor',
            'proximity_sensor',
            'servo_sensor',
            'vibration_sensor',
            'relay_sensor',
            'nrf24l01_sensor',
            'gps_sensor'
        ]
        
        sensors_dir = Path(__file__).parent
        
        for sensor_file in sensor_files:
            try:
                # Check if file exists
                file_path = sensors_dir / f"{sensor_file}.py"
                if not file_path.exists():
                    logger.warning(f"Sensor file not found: {sensor_file}.py")
                    continue
                
                # Import the module
                module_name = f"sensors.{sensor_file}"
                module = importlib.import_module(module_name)
                
                # Get the Sensor class from the module
                if hasattr(module, 'Sensor'):
                    sensor_class = getattr(module, 'Sensor')
                    
                    # Extract sensor metadata without creating a full instance
                    # Use class methods that don't require communication service
                    try:
                        # Create a minimal mock instance to get metadata without calling _register_callback
                        class MetadataOnlySensor(sensor_class):
                            def __init__(self):
                                # Skip the parent __init__ to avoid communication service requirement
                                pass
                        
                        metadata_instance = MetadataOnlySensor() 
                        sensor_id = metadata_instance.get_sensor_id()
                        sensor_name = metadata_instance.get_name()
                        data_fields = metadata_instance.get_data_fields()
                        units = metadata_instance.get_units()
                        
                        self.sensor_classes[sensor_id] = {
                            'class': sensor_class,
                            'name': sensor_name,
                            'module': sensor_file,
                            'data_fields': data_fields,
                            'units': units
                        }
                        
                        logger.info(f"Loaded sensor: {sensor_name} ({sensor_id})")
                    except Exception as e:
                        logger.error(f"Failed to extract metadata from {sensor_file}: {e}")
                else:
                    logger.error(f"No 'Sensor' class found in {sensor_file}.py")
                    
            except Exception as e:
                logger.error(f"Failed to load sensor {sensor_file}: {e}")
    
    def get_all_sensor_ids(self) -> List[str]:
        """Get list of all sensor IDs"""
        return list(self.sensor_classes.keys())
    
    def get_all_sensor_names(self) -> List[str]:
        """Get list of all sensor names"""
        return [info['name'] for info in self.sensor_classes.values()]
    
    def get_sensor_info(self, sensor_id: str) -> Dict[str, Any]:
        """Get sensor information by ID"""
        return self.sensor_classes.get(sensor_id, {})
    
    def get_sensor_class(self, sensor_id: str) -> Type:
        """Get sensor class by ID"""
        info = self.sensor_classes.get(sensor_id)
        return info['class'] if info else None
    
    def create_sensor_instance(self, sensor_id: str, communication_service):
        """Create an instance of a sensor"""
        sensor_class = self.get_sensor_class(sensor_id)
        if sensor_class:
            return sensor_class(communication_service)
        return None
    
    def get_sensor_count(self) -> int:
        """Get total number of registered sensors"""
        return len(self.sensor_classes)

# Global registry instance
sensor_registry = SensorRegistry()