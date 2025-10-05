# services/communication_service.py
"""
Communication service for serial communication with microcontrollers.
Passively listens to any device printing to the configured serial port at the specified baud rate.
Uses line buffering and runs on a separate thread to prevent GUI lag.
"""

import threading
import time
from abc import ABC, abstractmethod
from collections import deque
import serial
import sys
from pathlib import Path

# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class BaseCommunication(ABC):
    """Abstract base class for all communication implementations."""
    
    def __init__(self):
        self.sensor_discovery_callback = None
        self.sensor_data_callbacks = {}  # {sensor_name: callback_function}
        
    @abstractmethod
    def start(self):
        """Start the communication service."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the communication service."""
        pass
    
    @abstractmethod
    def close(self):
        """Close and cleanup the communication service."""
        pass
    
    def set_discovery_callback(self, callback):
        """
        Set callback to be called when new sensor is discovered.
        Callback signature: callback(sensor_name: str, pins: list, payload: str)
        """
        self.sensor_discovery_callback = callback
    
    def register_data_callback(self, sensor_name, callback):
        """
        Register a callback for sensor data.
        Callback signature: callback(data_values: list)
        """
        self.sensor_data_callbacks[sensor_name] = callback
        logger.debug(f"Registered data callback for sensor: {sensor_name}")
    
    def deregister_data_callback(self, sensor_name):
        """Deregister a callback for sensor data."""
        if sensor_name in self.sensor_data_callbacks:
            del self.sensor_data_callbacks[sensor_name]
            logger.debug(f"Deregistered data callback for sensor: {sensor_name}")


class PySerialCommunication(BaseCommunication):
    """
    PySerial-based communication that passively listens to serial output.
    Detects sensors via header format: *H*_sensorName_pinList_payload
    """
    
    def __init__(self, port, baudrate=9600, timeout=1.0, buffer_size=100):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.buffer_size = buffer_size
        
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        self.line_buffer = deque(maxlen=buffer_size)
        self.discovered_sensors = {}  # {sensor_name: {'pins': [], 'last_seen': timestamp}}
        
        logger.info(f"PySerialCommunication initialized for port {port} at {baudrate} baud")
    
    def start(self):
        """Start the serial communication and reading thread."""
        if self.running:
            logger.warning("Communication already running")
            return
        
        self.running = True
        self._connect()
        
        # Start reading thread
        self.read_thread = threading.Thread(target=self._read_loop, name="SerialReadThread", daemon=True)
        self.read_thread.start()
        logger.info("Serial reading thread started")
    
    def stop(self):
        """Stop the reading thread."""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
        logger.info("Serial reading thread stopped")
    
    def close(self):
        """Close the serial connection."""
        self.stop()
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info(f"Serial connection to {self.port} closed")
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")
        self.serial_conn = None
    
    def _connect(self):
        """Attempt to connect to the serial port."""
        try:
            logger.info(f"Attempting to connect to serial port {self.port} at {self.baudrate} baud")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            # Wait for Arduino to reset (if applicable)
            time.sleep(2)
            # Clear any startup noise
            self.serial_conn.reset_input_buffer()
            logger.info(f"Successfully connected to {self.port}")
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to serial port {self.port}: {e}")
            self.serial_conn = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to serial: {e}")
            self.serial_conn = None
    
    def _read_loop(self):
        """
        Main reading loop that runs on a separate thread.
        Uses read_until() to read complete lines with buffering.
        """
        logger.info("Serial read loop started")
        
        while self.running:
            # Check if connected
            if not self.serial_conn or not self.serial_conn.is_open:
                logger.warning("Serial connection lost, attempting to reconnect...")
                time.sleep(2)
                self._connect()
                continue
            
            try:
                # Read until newline character (blocking with timeout)
                line_bytes = self.serial_conn.read_until(b'\n')
                
                if line_bytes:
                    try:
                        # Decode and strip whitespace
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                        
                        if line:
                            # Add to buffer
                            self.line_buffer.append(line)
                            
                            # Process the line
                            self._process_line(line)
                            
                    except UnicodeDecodeError:
                        # Skip lines that can't be decoded
                        logger.debug("Skipped line with decode error")
                        continue
                        
            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                # Close and try to reconnect
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error in read loop: {e}")
                time.sleep(0.1)
        
        logger.info("Serial read loop stopped")
    
    def _process_line(self, line):
        """Process a received line - either header or data."""
        try:
            # Check if this is a header message
            if line.startswith('*H*_'):
                self._parse_header(line)
            else:
                # Regular data message (sensor_name:value1,value2,...)
                self._parse_data(line)
                
        except Exception as e:
            logger.debug(f"Error processing line '{line}': {e}")
    
    def _parse_header(self, header_line):
        """
        Parse header format: *H*_sensorName_pinList_payload
        Example: *H*_temperature_A0_temp:25.5C
        """
        try:
            # Remove *H*_ prefix
            content = header_line[4:]
            parts = content.split('_', 2)
            
            if len(parts) < 3:
                logger.warning(f"Invalid header format (expected 3 parts): {header_line}")
                return
            
            sensor_name = parts[0].strip()
            pin_list_str = parts[1].strip()
            payload = parts[2].strip()
            
            # Parse pin list
            pins = [pin.strip() for pin in pin_list_str.split(',') if pin.strip()]
            
            # Check if this is a new sensor
            is_new = sensor_name not in self.discovered_sensors
            
            # Update discovered sensors
            self.discovered_sensors[sensor_name] = {
                'pins': pins,
                'last_seen': time.time(),
                'last_payload': payload
            }
            
            if is_new:
                logger.info(f"New sensor discovered: '{sensor_name}' on pins {pins}")
                # Notify discovery callback
                if self.sensor_discovery_callback:
                    self.sensor_discovery_callback(sensor_name, pins, payload)
            
            # Also process the payload as data
            if sensor_name in self.sensor_data_callbacks:
                # Extract just the values from payload (e.g., "temp:25.5C" -> ["25.5"])
                data_values = self._extract_values_from_payload(payload)
                self.sensor_data_callbacks[sensor_name](data_values)
                
        except Exception as e:
            logger.error(f"Error parsing header '{header_line}': {e}")
    
    def _parse_data(self, data_line):
        """
        Parse regular data line format: sensor_name:value1,value2,...
        Example: temperature:25.6
        """
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
            logger.debug(f"Error parsing data line '{data_line}': {e}")
    
    def _extract_values_from_payload(self, payload):
        """
        Extract numeric/value parts from payload.
        Examples:
            "temp:25.5C" -> ["25.5"]
            "x:0.02,y:-0.01,z:9.81" -> ["0.02", "-0.01", "9.81"]
        """
        values = []
        parts = payload.split(',')
        for part in parts:
            if ':' in part:
                # Extract value after colon
                value = part.split(':', 1)[1]
                # Remove units (letters at the end)
                value_clean = ''.join(c for c in value if c.isdigit() or c in '.-')
                if value_clean:
                    values.append(value_clean)
            else:
                values.append(part.strip())
        return values
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return list(self.discovered_sensors.keys())
    
    def get_buffer_lines(self, n=10):
        """Get the last n lines from the buffer."""
        return list(self.line_buffer)[-n:]


class CommunicationService:
    """
    High-level communication service that manages serial or mock communication.
    This is the main interface used by the application.
    """
    
    def __init__(self, config):
        """
        Initialize the communication service.
        
        Args:
            config: CommunicationConfig object with port, baudrate, timeout, use_mock
        """
        self.config = config
        self.comm = None
        
        # Choose implementation based on config
        if config.use_mock or config.port == 'loop://' or config.port.startswith('mock'):
            logger.info("Using MockCommunication (simulated sensor data)")
            from sensors.mock_communication import MockCommunication
            self.comm = MockCommunication()
        else:
            logger.info(f"Using PySerialCommunication on port {config.port}")
            self.comm = PySerialCommunication(
                port=config.port,
                baudrate=config.baudrate,
                timeout=config.timeout / 1000.0  # Convert ms to seconds
            )
        
        # Start communication
        self.comm.start()
        logger.info("Communication service initialized and started")
    
    def set_discovery_callback(self, callback):
        """Set callback for sensor discovery."""
        return self.comm.set_discovery_callback(callback)
    
    def register_data_callback(self, sensor_name, callback):
        """Register callback for sensor data."""
        return self.comm.register_data_callback(sensor_name, callback)
    
    def deregister_data_callback(self, sensor_name):
        """Deregister callback for sensor data."""
        return self.comm.deregister_data_callback(sensor_name)
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return self.comm.get_discovered_sensors()
    
    def get_buffer_lines(self, n=10):
        """Get the last n lines from the buffer."""
        return self.comm.get_buffer_lines(n)
    
    def close(self):
        """Close and cleanup the communication service."""
        if self.comm:
            self.comm.close()
            logger.info("Communication service closed")
