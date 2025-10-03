# sensors/base_sensor.py
from datetime import datetime
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from services.communication_service import CommunicationService
from utils.data_processing import clean_sensor_data, validate_sensor_data
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class BaseSensor(ABC):
    """Abstract base class for all sensors."""
    
    def __init__(self, communication_service: CommunicationService):
        self.communication_service = communication_service
        self.name = self.get_name()
        self.sensor_id = self.get_sensor_id()
        self.data_fields = self.get_data_fields()
        self.units = self.get_units()
        self.data: List[Dict[str, Any]] = []
        self._is_active = False
        self._register_callback()
        logger.debug(f"Initialized sensor: {self.name}")
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the sensor name."""
        pass
    
    @abstractmethod
    def get_sensor_id(self) -> str:
        """Get the sensor ID for communication."""
        pass
    
    @abstractmethod
    def get_data_fields(self) -> List[str]:
        """Get the list of data field names."""
        pass
    
    def get_units(self) -> Dict[str, str]:
        """Get units for each data field. Override in subclasses."""
        return {field: "" for field in self.data_fields}
    
    def _register_callback(self) -> None:
        """Register callback with communication service."""
        try:
            self.communication_service.register_callback(
                self.sensor_id, 
                self.data_callback
            )
            self._is_active = True
            logger.debug(f"Registered callback for sensor {self.name}")
        except Exception as e:
            logger.error(f"Failed to register callback for sensor {self.name}: {e}")
            self._is_active = False
    
    def data_callback(self, values: List[str]) -> None:
        """Handle incoming sensor data."""
        try:
            # Create data dictionary
            data_dict = {'Time': datetime.now()}
            
            # Parse values
            for field_name, value_str in zip(self.data_fields, values):
                try:
                    data_dict[field_name] = float(value_str)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid value for {field_name} in {self.name}: {value_str}")
                    data_dict[field_name] = 0.0
            
            # Validate data
            if validate_sensor_data(data_dict):
                self.data.append(data_dict)
                # Keep only recent data (last 1000 points)
                if len(self.data) > 1000:
                    self.data = self.data[-1000:]
                logger.debug(f"Added data point for sensor {self.name}")
            else:
                logger.warning(f"Invalid data structure for sensor {self.name}: {data_dict}")
                
        except Exception as e:
            logger.error(f"Error processing data for sensor {self.name}: {e}")
    
    def get_data(self) -> pd.DataFrame:
        """Get sensor data as a pandas DataFrame."""
        try:
            df = pd.DataFrame(self.data)
            return clean_sensor_data(df) if not df.empty else df
        except Exception as e:
            logger.error(f"Error getting data for sensor {self.name}: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get the most recent data point."""
        try:
            return self.data[-1] if self.data else None
        except Exception as e:
            logger.error(f"Error getting latest data for sensor {self.name}: {e}")
            return None
    
    def clear_data(self) -> None:
        """Clear all stored data."""
        self.data.clear()
        logger.debug(f"Cleared data for sensor {self.name}")
    
    def is_active(self) -> bool:
        """Check if sensor is active and receiving data."""
        return self._is_active and bool(self.data)
    
    def start(self) -> bool:
        """Start the sensor. Override in subclasses if needed."""
        if not self._is_active:
            self._register_callback()
        return self._is_active
    
    def stop(self) -> bool:
        """Stop the sensor. Override in subclasses if needed."""
        try:
            self.communication_service.deregister_callback(self.sensor_id)
            self._is_active = False
            logger.debug(f"Stopped sensor {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping sensor {self.name}: {e}")
            return False
    
    def close(self) -> None:
        """Close the sensor and cleanup resources."""
        self.stop()
        self.clear_data()
        logger.debug(f"Closed sensor {self.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get sensor status information."""
        latest_data = self.get_latest_data()
        return {
            'name': self.name,
            'sensor_id': self.sensor_id,
            'is_active': self.is_active(),
            'data_points': len(self.data),
            'last_update': latest_data['Time'] if latest_data else None,
            'data_fields': self.data_fields,
            'units': self.units
        }