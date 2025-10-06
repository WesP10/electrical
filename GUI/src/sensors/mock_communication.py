# Mock communication for development and testing
import random
import time
import math
from threading import Thread
from collections import deque
from typing import Dict, Callable, List

from services.communication_service import BaseCommunication
from sensors.sensor_registry import sensor_registry
import sys
from pathlib import Path
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class MockCommunication(BaseCommunication):
    """
    Mock communication implementation for development and testing.
    Simulates sensor data for testing without actual hardware.
    """
    
    def __init__(self, port: str = None, baudrate: int = 9600, buffer_size: int = 1000):
        super().__init__()
        self.port = port or "mock://test"
        self.baudrate = baudrate
        self.running = False
        self.thread = None
        self.discovered_sensors = {}
        self.line_buffer = deque(maxlen=buffer_size)
        
        # Build available sensors from sensor registry
        self.available_sensors = {}
        for sensor_id, info in sensor_registry.sensor_classes.items():
            self.available_sensors[sensor_id] = {
                'name': info['name'],
                'data_fields': info['data_fields'],
                'units': info['units'],
                'pins': self._get_default_pins(sensor_id),
                'send_header_count': 0
            }
        
        logger.info('MockCommunication initialized for development/testing')
        logger.info(f'Mock sensors: {list(self.available_sensors.keys())}')
    
    def _get_default_pins(self, sensor_id: str) -> List[str]:
        """Get default pin assignments for different sensor types"""
        pin_mapping = {
            'ULTRASONIC_SENSOR': ['D7', 'D8'],
            'ACCEL_SENSOR': ['A1', 'D2', 'D3'],
            'PRESSURE_SENSOR': ['A2'],
            'TEMP_SENSOR': ['A0'],
            'THERMISTOR_SENSOR': ['A0'],
            'LINE_SENSOR': ['A0'],
            'PROXIMITY_SENSOR': ['A0'],
            'SERVO_SENSOR': ['D9'],
            'VIBRATION_SENSOR': ['D2'],
            'RELAY_SENSOR': ['D4'],
            'NRF24L01_SENSOR': ['D10', 'D9', 'D2'],
            'GPS_SENSOR': ['D0', 'D1']
        }
        return pin_mapping.get(sensor_id, ['A0'])

    def start(self):
        """Start the mock data generation"""
        if not self.running:
            self.running = True
            
            # Auto-discover all available sensors at startup
            for sensor_id, sensor_info in self.available_sensors.items():
                if sensor_id not in self.discovered_sensors:
                    self.discovered_sensors[sensor_id] = {
                        'pins': sensor_info['pins']
                    }
                    logger.info(f'Mock: New sensor discovered: {sensor_id} on pins {sensor_info["pins"]}')
            
            self.thread = Thread(target=self._generate_data_loop, daemon=True)
            self.thread.start()
            logger.info('Mock data generation started')
from typing import Dict, Callable, List

from services.communication_service import BaseCommunication
from sensors.sensor_registry import sensor_registry
import sys
from pathlib import Path
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class MockCommunication(BaseCommunication):
    """
    Mock communication implementation for development and testing.
    Simulates a microcontroller sending serial data with headers.
    """
    
    def __init__(self, buffer_size=100):
        super().__init__()
        self.running = False
        self.thread = None
        self.discovered_sensors = {}
        self.line_buffer = deque(maxlen=buffer_size)
        
        # Build available sensors from sensor registry
        self.available_sensors = {}
        for sensor_id, info in sensor_registry.sensor_classes.items():
            self.available_sensors[sensor_id] = {
                'name': info['name'],
                'data_fields': info['data_fields'],
                'units': info['units'],
                'pins': self._get_default_pins(sensor_id),
                'send_header_count': 0
            }
        
        logger.info('MockCommunication initialized for development/testing')
        logger.info(f'Mock sensors: {list(self.available_sensors.keys())}')
    
    def _get_default_pins(self, sensor_id: str) -> List[str]:
        """Get default pin assignments for different sensor types"""
        pin_mapping = {
            'ULTRASONIC_SENSOR': ['D7', 'D8'],
            'ACCEL_SENSOR': ['A1', 'D2', 'D3'],
            'PRESSURE_SENSOR': ['A2'],
            'TEMP_SENSOR': ['A0'],
            'THERMISTOR_SENSOR': ['A0'],
            'LINE_SENSOR': ['A0'],
            'PROXIMITY_SENSOR': ['A0'],
            'SERVO_SENSOR': ['D9'],
            'VIBRATION_SENSOR': ['D2'],
            'RELAY_SENSOR': ['D4'],
            'NRF24L01_SENSOR': ['D10', 'D9', 'D2'],
            'GPS_SENSOR': ['D0', 'D1']
        }
        return pin_mapping.get(sensor_id, ['A0'])
    
    def start(self):
        """Start the mock data generation"""
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._generate_mock_data, daemon=True, name="MockDataThread")
            self.thread.start()
            logger.info('Mock data generation started')
    
    def stop(self):
        """Stop the mock data generation"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info('Mock data generation stopped')
    
    def close(self):
        """Close the mock communication"""
        self.stop()
        logger.info('MockCommunication closed')
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return list(self.discovered_sensors.keys())
    
    def get_buffer_lines(self, n=10):
        """Get the last n lines from the buffer."""
        return list(self.line_buffer)[-n:]
    
    def set_discovery_callback(self, callback: Callable[[str, List[str], str], None]) -> None:
        """Set the discovery callback and notify for existing sensors"""
        self.discovery_callback = callback
        logger.info("Mock: Discovery callback set")
        
        # Notify callback for already-discovered sensors (make a copy to avoid iteration issues)
        existing_sensors = dict(self.discovered_sensors)
        for sensor_id, sensor_info in existing_sensors.items():
            logger.info(f"Mock: Notifying callback for existing sensor: {sensor_id}")
            # Include an empty payload for discovery callback (payload is from data messages, not discovery)
            callback(sensor_id, sensor_info['pins'], "")
    
    def _generate_mock_data(self):
        """
        Generate mock sensor data continuously with header format.
        Simulates a microcontroller printing to serial.
        """
        logger.info("Mock data generation loop started")
        
        while self.running:
            try:
                for sensor_id, sensor_info in self.available_sensors.items():
                    pins_str = ','.join(sensor_info['pins'])
                    
                    # Send header periodically (every 10 iterations)
                    if sensor_info['send_header_count'] % 10 == 0:
                        header_line = self._generate_header(sensor_id, pins_str)
                        if header_line:
                            self.line_buffer.append(header_line)
                            self._process_line(header_line)
                    else:
                        # Send regular data without header (faster updates)
                        data_line = self._generate_data(sensor_id)
                        if data_line:
                            self.line_buffer.append(data_line)
                            self._process_line(data_line)
                    
                    sensor_info['send_header_count'] += 1
                
                # Sleep for realistic serial timing (100ms = 10Hz)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f'Error in mock data generation: {e}')
                time.sleep(1)
        
        logger.info("Mock data generation loop stopped")
    
    def _generate_header(self, sensor_id, pins_str):
        """Generate a header line for a sensor."""
        sensor_info = self.available_sensors.get(sensor_id)
        if not sensor_info:
            return None
            
        payload = self._generate_payload_by_sensor_id(sensor_id)
        return f'*H*_{sensor_id}_{pins_str}_{payload}'
    
    def _generate_data(self, sensor_id):
        """Generate a regular data line for a sensor."""
        sensor_info = self.available_sensors.get(sensor_id)
        if not sensor_info:
            return None
            
        payload = self._generate_payload_by_sensor_id(sensor_id)
        return f'{sensor_id}:{payload}'
    
    def _generate_payload_by_sensor_id(self, sensor_id):
        """Generate realistic payload data based on sensor ID"""
        current_time = time.time()
        sensor_info = self.available_sensors.get(sensor_id)
        data_fields = sensor_info['data_fields'] if sensor_info else ['value']
        
        if sensor_id == 'ULTRASONIC_SENSOR':
            distance = 2 + 50 * random.random() + 10 * math.sin(current_time / 5)
            return f'distance:{round(distance, 2)}'
            
        elif sensor_id == 'ACCEL_SENSOR':
            x = random.gauss(0, 0.1)
            y = random.gauss(0, 0.1)
            z = random.gauss(9.8, 0.2)
            return f'x:{round(x,3)},y:{round(y,3)},z:{round(z,3)}'
            
        elif sensor_id == 'PRESSURE_SENSOR':
            pressure = 1013.25 + random.gauss(0, 5)
            return f'pressure:{round(pressure, 2)}'
            
        elif sensor_id in ['TEMP_SENSOR', 'THERMISTOR_SENSOR']:
            temp = 20 + 10 * random.random() + 5 * math.sin(current_time / 10)
            return f'temperature:{round(temp, 2)}'
            
        elif sensor_id == 'LINE_SENSOR':
            value = random.randint(0, 1023)
            detected = 1 if value < 200 else 0
            return f'value:{value},detected:{detected}'
            
        elif sensor_id == 'PROXIMITY_SENSOR':
            distance = 5 + 30 * random.random()
            signal_strength = max(0, 100 - distance * 2)
            return f'distance:{round(distance,1)},signal_strength:{round(signal_strength,1)}'
            
        elif sensor_id == 'SERVO_SENSOR':
            angle = 90 + 45 * math.sin(current_time / 3)
            current = 50 + random.randint(-10, 10)
            return f'angle:{round(angle,1)},current:{current}'
            
        elif sensor_id == 'VIBRATION_SENSOR':
            intensity = 0.1 + 0.9 * random.random()
            frequency = 10 + 40 * random.random()
            return f'intensity:{round(intensity,3)},frequency:{round(frequency,1)}'
            
        elif sensor_id == 'RELAY_SENSOR':
            state = random.choice([0, 1])
            voltage = 3.3 if state else 0.0
            return f'state:{state},voltage:{voltage}'
            
        elif sensor_id == 'NRF24L01_SENSOR':
            signal_strength = -30 - random.randint(0, 40)
            data_rate = random.choice([250, 1000, 2000])
            packet_count = random.randint(50, 200)
            return f'signal_strength:{signal_strength},data_rate:{data_rate},packet_count:{packet_count}'
            
        elif sensor_id == 'GPS_SENSOR':
            lat = 42.3601 + random.gauss(0, 0.001)
            lon = -71.0589 + random.gauss(0, 0.001)
            alt = 10 + random.gauss(0, 2)
            return f'latitude:{round(lat,6)},longitude:{round(lon,6)},altitude:{round(alt,1)}'
            
        else:
            # Generic fallback
            if len(data_fields) == 1:
                value = 50 + 25 * random.random() + 10 * math.sin(current_time / 8)
                return f'{data_fields[0]}:{round(value, 2)}'
            else:
                # Multiple fields - generate random values
                values = []
                for field in data_fields:
                    value = 10 + 20 * random.random()
                    values.append(f'{field}:{round(value, 2)}')
                return ','.join(values)
    
    def close(self):
        """Close and cleanup the mock communication."""
        self.running = False
        logger.info("Mock communication closed")
    
    def _process_line(self, line):
        """Process a line (header or data) and trigger appropriate callbacks."""
        try:
            # Check if this is a header message
            if line.startswith('*H*_'):
                self._parse_header(line)
            else:
                # Regular data message
                self._parse_data(line)
                
        except Exception as e:
            logger.debug(f"Error processing mock line '{line}': {e}")
    
    def _parse_header(self, header_line):
        """Parse header format: *H*_sensorName_pinList_payload"""
        try:
            content = header_line[4:]
            parts = content.split('_', 2)
            
            if len(parts) < 3:
                return
            
            sensor_name = parts[0].strip()
            pin_list = [pin.strip() for pin in parts[1].split(',') if pin.strip()]
            payload = parts[2].strip()
            
            # Update discovered sensors
            is_new = sensor_name not in self.discovered_sensors
            self.discovered_sensors[sensor_name] = {
                'pins': pin_list,
                'last_seen': time.time(),
                'payload': payload
            }
            
            if is_new:
                logger.info(f'Mock: New sensor discovered: {sensor_name} on pins {pin_list}')
                # Notify discovery callback
                if self.sensor_discovery_callback:
                    self.sensor_discovery_callback(sensor_name, pin_list, payload)
            
            # Trigger data callback with extracted values
            if sensor_name in self.sensor_data_callbacks:
                data_values = self._extract_values_from_payload(payload)
                self.sensor_data_callbacks[sensor_name](data_values)
                
        except Exception as e:
            logger.error(f'Error parsing mock header: {e}')
    
    def _parse_data(self, data_line):
        """Parse regular data line format: sensor_name:value1,value2,..."""
        try:
            if ':' not in data_line:
                return
            
            sensor_name, values_str = data_line.split(':', 1)
            sensor_name = sensor_name.strip()
            
            # Update last seen time
            if sensor_name in self.discovered_sensors:
                self.discovered_sensors[sensor_name]['last_seen'] = time.time()
            
            # Call data callback if registered
            if sensor_name in self.sensor_data_callbacks:
                data_values = [v.strip() for v in values_str.split(',')]
                self.sensor_data_callbacks[sensor_name](data_values)
                
        except Exception as e:
            logger.debug(f"Error parsing mock data line '{data_line}': {e}")
    
    def _extract_values_from_payload(self, payload):
        """Extract numeric values from payload like 'temp:25.5C' or 'x:0.02,y:-0.01,z:9.81'"""
        values = []
        parts = payload.split(',')
        for part in parts:
            if ':' in part:
                value = part.split(':', 1)[1]
                # Remove units (letters at the end)
                value_clean = ''.join(c for c in value if c.isdigit() or c in '.-')
                if value_clean:
                    values.append(value_clean)
            else:
                values.append(part.strip())
        return values
