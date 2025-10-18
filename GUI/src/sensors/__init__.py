# sensors/__init__.py
"""Sensors package for the Hyperloop GUI application."""
import os
import importlib
from typing import List, Type
from .base_sensor import BaseSensor
from services.communication_service import CommunicationService
import sys
from pathlib import Path
# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)


def load_sensors(communication_service: CommunicationService) -> List[BaseSensor]:
    """Load all available sensor implementations.
    
    Args:
        communication_service: The communication service instance
        
    Returns:
        List of initialized sensor instances
    """
    sensors = []
    sensor_folder = os.path.dirname(__file__)
    
    try:
        for filename in os.listdir(sensor_folder):
            if filename.endswith('_sensor.py') and filename != 'base_sensor.py':
                try:
                    module_name = f'sensors.{filename[:-3]}'
                    module = importlib.import_module(module_name)
                    sensor_class = getattr(module, 'Sensor', None)
                    
                    if sensor_class and issubclass(sensor_class, BaseSensor):
                        sensor_instance = sensor_class(communication_service)
                        sensors.append(sensor_instance)
                        logger.debug(f"Loaded sensor: {sensor_instance.name}")
                    else:
                        logger.warning(f"No valid Sensor class found in {module_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load sensor from {filename}: {e}")
                    
    except Exception as e:
        logger.error(f"Error loading sensors from {sensor_folder}: {e}")
    
    logger.info(f"Loaded {len(sensors)} sensors")
    return sensors


def get_available_sensor_types() -> List[Type[BaseSensor]]:
    """Get all available sensor types without instantiating them.
    
    Returns:
        List of sensor classes
    """
    sensor_types = []
    sensor_folder = os.path.dirname(__file__)
    
    try:
        for filename in os.listdir(sensor_folder):
            if filename.endswith('_sensor.py') and filename != 'base_sensor.py':
                try:
                    module_name = f'sensors.{filename[:-3]}'
                    module = importlib.import_module(module_name)
                    sensor_class = getattr(module, 'Sensor', None)
                    
                    if sensor_class and issubclass(sensor_class, BaseSensor):
                        sensor_types.append(sensor_class)
                        
                except Exception as e:
                    logger.error(f"Failed to load sensor type from {filename}: {e}")
                    
    except Exception as e:
        logger.error(f"Error getting sensor types from {sensor_folder}: {e}")
    
    return sensor_types