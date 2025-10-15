"""Sensor service for managing sensor operations with dynamic discovery."""
from typing import List, Dict, Optional
import time
import threading
from datetime import datetime
import pandas as pd

import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger
from services.communication_service import CommunicationService

logger = get_logger(__name__)


class DynamicSensor:
    """Dynamically created sensor that holds data."""
    
    def __init__(self, name: str, pins: List[str]):
        self.name = name
        self.pins = pins
        self.data: List[Dict] = []
        self._is_active = True
        self.last_update = time.time()
    
    def update_data(self, payload: str):
        """Add new data from payload."""
        try:
            data_dict = {'Time': datetime.now()}
            
            # Parse payload into separate values
            # Format examples: "25.5" or "0.03,-0.02,9.80" or "temp:25.5C"
            values = payload.split(',')
            
            if len(values) == 1:
                # Single value - extract number
                value_str = values[0]
                # Remove any labels (e.g., "temp:25.5C" -> "25.5")
                if ':' in value_str:
                    value_str = value_str.split(':', 1)[1]
                # Remove units (letters at end)
                value_clean = ''.join(c for c in value_str if c.isdigit() or c in '.-')
                try:
                    data_dict['value'] = float(value_clean) if value_clean else 0.0
                except ValueError:
                    data_dict['value'] = 0.0
            else:
                # Multiple values
                for i, val in enumerate(values):
                    # Extract number from each value
                    val_str = val.strip()
                    if ':' in val_str:
                        val_str = val_str.split(':', 1)[1]
                    val_clean = ''.join(c for c in val_str if c.isdigit() or c in '.-')
                    try:
                        data_dict[f'value_{i}'] = float(val_clean) if val_clean else 0.0
                    except ValueError:
                        data_dict[f'value_{i}'] = 0.0
            
            self.data.append(data_dict)
            # Keep only recent data (last 1000 points)
            if len(self.data) > 1000:
                self.data = self.data[-1000:]
            self.last_update = time.time()
        except Exception as e:
            logger.error(f"Error updating data for {self.name}: {e}")
    
    def get_data(self) -> pd.DataFrame:
        """Get sensor data as DataFrame."""
        try:
            if not self.data:
                return pd.DataFrame()
            return pd.DataFrame(self.data)
        except Exception as e:
            logger.error(f"Error getting data for {self.name}: {e}")
            return pd.DataFrame()
    
    def is_active(self) -> bool:
        """Check if sensor is active."""
        return self._is_active
    
    def set_active(self, active: bool):
        """Set sensor active status."""
        self._is_active = active


class SensorService:
    """Service for managing sensors with dynamic discovery and watchdog timers."""
    
    # Watchdog timeout in seconds - sensor marked unavailable if no data received
    WATCHDOG_TIMEOUT = 3.0  # Reduced from 5.0 for faster disconnection detection
    
    def __init__(self, communication_service: CommunicationService):
        self.communication_service = communication_service
        self._sensors: Dict[str, DynamicSensor] = {}  # {sensor_name: sensor_object}
        self._watchdog_timers: Dict[str, float] = {}  # {sensor_name: last_seen_timestamp}
        self._sensor_availability: Dict[str, bool] = {}  # {sensor_name: is_available}
        self._watchdog_thread = None
        self._watchdog_running = False
        
        # Set up discovery callback
        self.communication_service.set_discovery_callback(self._on_sensor_discovered)
        logger.info("Sensor discovery callback registered")
        
        # Start watchdog timer thread
        self._start_watchdog()
        
        logger.info("Sensor service initialized with passive discovery mode")
        logger.info(f"Watchdog timeout: {self.WATCHDOG_TIMEOUT}s")
        logger.info("Waiting for sensors to announce themselves via headers...")
    
    def _on_sensor_discovered(self, sensor_name: str, pins: List[str], payload: str):
        """Callback when a new sensor is discovered via header."""
        logger.info(f"Discovery callback triggered: {sensor_name}")
        if sensor_name not in self._sensors:
            # Create new dynamic sensor
            sensor = DynamicSensor(sensor_name, pins)
            self._sensors[sensor_name] = sensor
            self._sensor_availability[sensor_name] = True
            self._watchdog_timers[sensor_name] = time.time()
            
            # Register callback for this sensor's data
            self.communication_service.register_data_callback(
                sensor_name,
                lambda data: self._on_sensor_data(sensor_name, data)
            )
            
            logger.info(f"✓ New sensor discovered: {sensor_name} on pins {pins}")
        else:
            # Update existing sensor timestamp
            self._watchdog_timers[sensor_name] = time.time()
            if not self._sensor_availability.get(sensor_name, False):
                self._sensor_availability[sensor_name] = True
                self._sensors[sensor_name].set_active(True)
                logger.info(f"↻ Sensor {sensor_name} is now available again")
    
    def _on_sensor_data(self, sensor_name: str, data_values: List[str]):
        """Callback when sensor data is received."""
        if sensor_name in self._sensors:
            # Update watchdog timer
            self._watchdog_timers[sensor_name] = time.time()
            
            # Update sensor data
            payload = ','.join(data_values) if isinstance(data_values, list) else str(data_values)
            self._sensors[sensor_name].update_data(payload)
            
            # Mark as available if it wasn't
            if not self._sensor_availability.get(sensor_name, False):
                self._sensor_availability[sensor_name] = True
                self._sensors[sensor_name].set_active(True)
    
    def _start_watchdog(self):
        """Start the watchdog timer thread."""
        self._watchdog_running = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()
        logger.debug("Watchdog timer thread started")
    
    def _watchdog_loop(self):
        """Watchdog timer loop - marks sensors as unavailable if no data received."""
        while self._watchdog_running:
            try:
                current_time = time.time()
                
                for sensor_name, last_seen in list(self._watchdog_timers.items()):
                    if current_time - last_seen > self.WATCHDOG_TIMEOUT:
                        # Watchdog timeout - mark sensor as unavailable
                        if self._sensor_availability.get(sensor_name, True):
                            self._sensor_availability[sensor_name] = False
                            if sensor_name in self._sensors:
                                self._sensors[sensor_name].set_active(False)
                            logger.warning(f"⏱ Sensor '{sensor_name}' marked unavailable (watchdog timeout)")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in watchdog loop: {e}")
                time.sleep(1)
    
    def get_sensors(self) -> List[DynamicSensor]:
        """Get all discovered sensors."""
        return list(self._sensors.values())
    
    def get_sensor(self, name: str) -> Optional[DynamicSensor]:
        """Get a specific sensor by name."""
        return self._sensors.get(name)
    
    def get_sensor_names(self) -> List[str]:
        """Get names of all discovered sensors."""
        return list(self._sensors.keys())
    
    def get_available_sensor_names(self) -> List[str]:
        """Get names of currently available sensors (not timed out)."""
        return [name for name, available in self._sensor_availability.items() if available]
    
    def is_sensor_available(self, sensor_name: str) -> bool:
        """Check if a sensor is currently available (not timed out)."""
        return self._sensor_availability.get(sensor_name, False)
    
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
        for sensor_name in self._sensors.keys():
            sensor_data = self.get_sensor_data(sensor_name)
            if sensor_data is not None and not sensor_data.empty:
                data[sensor_name] = sensor_data
        return data
    
    def shutdown(self) -> None:
        """Shutdown the sensor service."""
        logger.info("Shutting down sensor service...")
        
        # Stop watchdog
        self._watchdog_running = False
        if self._watchdog_thread:
            self._watchdog_thread.join(timeout=2)
        
        # Deregister all sensor callbacks
        for sensor_name in list(self._sensors.keys()):
            try:
                self.communication_service.deregister_data_callback(sensor_name)
            except Exception as e:
                logger.error(f"Error deregistering callback for {sensor_name}: {e}")
        
        # Clear all data
        self._sensors.clear()
        self._watchdog_timers.clear()
        self._sensor_availability.clear()
        
        logger.info("Sensor service shutdown complete")
    
    def clear_all_sensors(self) -> None:
        """Clear all sensors and their data (used when switching microcontrollers)."""
        logger.info("Clearing all sensors for microcontroller switch...")
        
        # Deregister all sensor callbacks
        for sensor_name in list(self._sensors.keys()):
            try:
                self.communication_service.deregister_data_callback(sensor_name)
            except Exception as e:
                logger.error(f"Error deregistering callback for {sensor_name}: {e}")
        
        # Clear all data structures
        self._sensors.clear()
        self._watchdog_timers.clear()
        self._sensor_availability.clear()
        
        logger.info("All sensors cleared successfully")