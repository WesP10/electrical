"""Sensor service for managing sensor operations."""
from typing import List, Dict, Optional, Type
import os
import importlib
from datetime import datetime
import pandas as pd

from config.log_config import get_logger
from core.exceptions import SensorError
from services.communication_service import CommunicationService

logger = get_logger(__name__)


class SensorService:
    """Service for managing sensors and their data."""
    
    def __init__(self, communication_service: CommunicationService):
        self.communication_service = communication_service
        self._sensors: List[object] = []
        self._sensor_registry: Dict[str, object] = {}
        self._load_sensors()
        logger.info(f"Sensor service initialized with {len(self._sensors)} sensors")
    
    def _load_sensors(self) -> None:
        """Load all available sensor implementations."""
        try:
            # Import the base sensor class
            from sensors.base_sensor import BaseSensor
            
            # Find all sensor files
            sensors_folder = os.path.join(os.path.dirname(__file__), '..', 'sensors')
            sensor_files = [
                f for f in os.listdir(sensors_folder) 
                if f.endswith('_sensor.py') and f != 'base_sensor.py'
            ]
            
            for sensor_file in sensor_files:
                try:
                    module_name = f'sensors.{sensor_file[:-3]}'
                    module = importlib.import_module(module_name)
                    
                    # Look for a Sensor class in the module
                    sensor_class = getattr(module, 'Sensor', None)
                    if sensor_class and issubclass(sensor_class, BaseSensor):
                        sensor_instance = sensor_class(self.communication_service)
                        self._sensors.append(sensor_instance)
                        self._sensor_registry[sensor_instance.name] = sensor_instance
                        logger.debug(f"Loaded sensor: {sensor_instance.name}")
                    else:
                        logger.warning(f"No valid Sensor class found in {module_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load sensor from {sensor_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load sensors: {e}")
            raise SensorError(f"Sensor loading failed: {e}")
    
    def get_sensors(self) -> List[object]:
        """Get all loaded sensors."""
        return self._sensors.copy()
    
    def get_sensor(self, name: str) -> Optional[object]:
        """Get a specific sensor by name."""
        return self._sensor_registry.get(name)
    
    def get_sensor_names(self) -> List[str]:
        """Get names of all loaded sensors."""
        return list(self._sensor_registry.keys())
    
    def get_sensor_data(self, sensor_name: str) -> Optional[pd.DataFrame]:
        """Get data from a specific sensor."""
        sensor = self.get_sensor(sensor_name)
        if not sensor:
            logger.warning(f"Sensor '{sensor_name}' not found")
            return None
        
        try:
            return sensor.get_data()
        except Exception as e:
            logger.error(f"Failed to get data from sensor '{sensor_name}': {e}")
            return None
    
    def get_all_sensor_data(self) -> Dict[str, pd.DataFrame]:
        """Get data from all sensors."""
        data = {}
        for sensor_name in self._sensor_registry.keys():
            sensor_data = self.get_sensor_data(sensor_name)
            if sensor_data is not None:
                data[sensor_name] = sensor_data
        return data
    
    def start_sensor(self, sensor_name: str) -> bool:
        """Start a specific sensor."""
        sensor = self.get_sensor(sensor_name)
        if not sensor:
            logger.warning(f"Sensor '{sensor_name}' not found")
            return False
        
        try:
            if hasattr(sensor, 'start'):
                sensor.start()
                logger.info(f"Sensor '{sensor_name}' started")
                return True
            else:
                logger.debug(f"Sensor '{sensor_name}' does not support start operation")
                return True
        except Exception as e:
            logger.error(f"Failed to start sensor '{sensor_name}': {e}")
            return False
    
    def stop_sensor(self, sensor_name: str) -> bool:
        """Stop a specific sensor."""
        sensor = self.get_sensor(sensor_name)
        if not sensor:
            logger.warning(f"Sensor '{sensor_name}' not found")
            return False
        
        try:
            if hasattr(sensor, 'stop'):
                sensor.stop()
                logger.info(f"Sensor '{sensor_name}' stopped")
                return True
            else:
                logger.debug(f"Sensor '{sensor_name}' does not support stop operation")
                return True
        except Exception as e:
            logger.error(f"Failed to stop sensor '{sensor_name}': {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown all sensors."""
        logger.info("Shutting down sensor service...")
        for sensor in self._sensors:
            try:
                if hasattr(sensor, 'close'):
                    sensor.close()
                elif hasattr(sensor, 'stop'):
                    sensor.stop()
                logger.debug(f"Sensor '{sensor.name}' shut down")
            except Exception as e:
                logger.error(f"Error shutting down sensor '{sensor.name}': {e}")
        
        self._sensors.clear()
        self._sensor_registry.clear()
        logger.info("Sensor service shutdown complete")