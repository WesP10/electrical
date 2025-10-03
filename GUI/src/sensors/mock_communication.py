# Mock communication for development and testing
import random
import time
import math
from threading import Thread
from datetime import datetime
from typing import Dict, Callable

from services.communication_service import BaseCommunication
from config.log_config import get_logger

logger = get_logger(__name__)


class MockCommunication(BaseCommunication):
    """Mock communication implementation for development and testing."""
    
    def __init__(self):
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self.thread = None
        logger.info("MockCommunication initialized for development/testing")
    
    def start(self):
        """Start the mock data generation"""
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._generate_mock_data, daemon=True)
            self.thread.start()
            logger.info("Mock data generation started")
    
    def stop(self):
        """Stop the mock data generation"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Mock data generation stopped")
    
    def send_command(self, command: str) -> bool:
        """Send a command (mock implementation)."""
        logger.info(f"Mock command sent: {command}")
        # Simulate successful command
        return True
    
    def register_callback(self, sensor_id: str, callback: Callable) -> None:
        """Register a callback for a sensor"""
        self.callbacks[sensor_id] = callback
        logger.debug(f"Registered callback for sensor: {sensor_id}")
        if not self.running:
            self.start()
    
    def deregister_callback(self, sensor_id: str) -> None:
        """Deregister a callback for a sensor"""
        if sensor_id in self.callbacks:
            del self.callbacks[sensor_id]
            logger.debug(f"Deregistered callback for sensor: {sensor_id}")
    
    def _generate_mock_data(self):
        """Generate mock sensor data continuously"""
        while self.running:
            try:
                # Generate mock data for different sensor types
                for sensor_id, callback in self.callbacks.items():
                    if sensor_id == 'TEMP_SENSOR':
                        # Temperature data (15-35°C)
                        temp = 20 + 10 * random.random() + 5 * math.sin(time.time() / 10)
                        callback([str(round(temp, 2))])
                    
                    elif sensor_id == 'ACCEL_SENSOR':
                        # Accelerometer data (3-axis)
                        x = random.gauss(0, 0.1)
                        y = random.gauss(0, 0.1) 
                        z = random.gauss(9.8, 0.2)  # Gravity + noise
                        callback([str(round(x, 3)), str(round(y, 3)), str(round(z, 3))])
                    
                    elif sensor_id == 'PRESSURE_SENSOR':
                        # Pressure data (atmospheric pressure with variations)
                        pressure = 1013.25 + random.gauss(0, 5)
                        callback([str(round(pressure, 2))])
                    
                    elif sensor_id == 'GPS_SENSOR':
                        # GPS data (latitude, longitude, altitude)
                        lat = 42.4534 + random.gauss(0, 0.0001)  # Cornell area
                        lon = -76.4735 + random.gauss(0, 0.0001)
                        alt = 250 + random.gauss(0, 5)
                        callback([str(round(lat, 6)), str(round(lon, 6)), str(round(alt, 1))])
                    
                    elif sensor_id == 'ULTRASONIC_SENSOR':
                        # Ultrasonic distance sensor (0-400cm)
                        distance = random.uniform(10, 400)
                        callback([str(round(distance, 1))])
                    
                    else:
                        # Generic sensor - single random value
                        value = random.uniform(0, 100)
                        callback([str(round(value, 2))])
                
                # Sleep for a bit before next update
                time.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in mock data generation: {e}")
                time.sleep(1)
    
    def close(self):
        """Close the mock communication"""
        self.stop()
        logger.info("MockCommunication closed")