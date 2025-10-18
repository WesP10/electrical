# sensors/communication.py
import threading
import time
from abc import ABC, abstractmethod
import serial
import sys
from pathlib import Path

# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)

class CommunicationInterface(ABC):
    def __init__(self):
        self.callbacks = {}  # {sensor_id: callback}

    def register_callback(self, sensor_id, callback):
        self.callbacks[sensor_id] = callback

    def deregister_callback(self, sensor_id):
        self.callbacks.pop(sensor_id, None)
    
    @abstractmethod
    def query_sensors(self):
        """Query for available sensors."""
        pass

    @abstractmethod
    def close(self):
        pass

class PySerialCommunication(CommunicationInterface):
    def __init__(self, port, baudrate=9600, timeout=1, reconnect_interval=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect_interval = reconnect_interval
        self.serial_conn = None
        self.running = True
        self.serial_lock = threading.Lock()
        self.discovered_sensors = {}  # {sensor_name: {'pins': [], 'last_seen': timestamp}}
        self.sensor_discovery_callback = None  # Callback when new sensor discovered
        self.thread = threading.Thread(target=self.read_loop, name="SerialReadThread")
        self.thread.daemon = True
        self.thread.start()

    def connect(self):
        retry_count = 0
        max_retries = 3  # Limit retries to avoid endless loops
        
        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Attempting to connect to serial port {self.port} (attempt {retry_count + 1}/{max_retries})")
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                time.sleep(2)  # Wait for Arduino to reset if necessary
                logger.info(f"[SUCCESS] Successfully connected to serial port {self.port}")
                break  # Exit the loop once connected
            except serial.SerialException as e:
                retry_count += 1
                logger.warning(f"[ERROR] Error connecting to serial port {self.port}: {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying in {self.reconnect_interval} seconds... ({retry_count}/{max_retries})")
                    time.sleep(self.reconnect_interval)
                else:
                    logger.error(f"[ERROR] Failed to connect after {max_retries} attempts.")
                    logger.error(f"[ERROR] No microcontroller detected on port {self.port}")
                    self.serial_conn = None
                    break
            except Exception as e:
                retry_count += 1
                logger.error(f"[ERROR] Unexpected error: {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying in {self.reconnect_interval} seconds... ({retry_count}/{max_retries})")
                    time.sleep(self.reconnect_interval)
                else:
                    logger.error(f"[ERROR] Failed to connect after {max_retries} attempts.")
                    logger.error(f"[ERROR] Hardware connection failed on port {self.port}")
                    self.serial_conn = None
                    break

    def read_loop(self):
        self.connect()
        
        while self.running:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    with self.serial_lock:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        logger.debug(f"Received line: {line}")
                        
                        # Check if this is a header message
                        if line.startswith('*H*_'):
                            self.parse_header(line)
                        else:
                            # Regular sensor data message
                            sensor_id, data_str = self.parse_message(line)
                            if sensor_id and sensor_id in self.callbacks:
                                data_values = data_str.split(',')
                                self.callbacks[sensor_id](data_values)
                                
                except serial.SerialException as e:
                    logger.warning(f"SerialException occurred: {e}")
                    logger.info("Closing connection and attempting to reconnect...")
                    with self.serial_lock:
                        try:
                            self.serial_conn.close()
                        except Exception as close_exception:
                            logger.error(f"Error closing serial connection: {close_exception}")
                        self.serial_conn = None
                    self.connect()
                except Exception as e:
                    logger.error(f"Unexpected error during read: {e}")
                    # Close the serial connection and attempt to reconnect
                    with self.serial_lock:
                        if self.serial_conn:
                            try:
                                self.serial_conn.close()
                            except Exception as close_exception:
                                logger.error(f"Error closing serial connection: {close_exception}")
                            self.serial_conn = None
                    self.connect()
            else:
                logger.debug("Serial connection is not open. Attempting to reconnect...")
                self.connect()
            time.sleep(0.01)  # Small delay for high-frequency updates

    def parse_message(self, message):
        parts = message.split(':', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        else:
            return None, None
    
    def parse_header(self, header_line):
        """Parse header format: *H*_sensorName_pinList_payload
        
        Example: *H*_accelerometer_A0,D3,D4_speed:5km/h
        """
        try:
            # Remove *H*_ prefix
            if not header_line.startswith('*H*_'):
                return
            
            content = header_line[4:]  # Remove '*H*_'
            parts = content.split('_', 2)  # Split into max 3 parts
            
            if len(parts) < 3:
                logger.warning(f"Invalid header format: {header_line}")
                return
            
            sensor_name = parts[0]
            pin_list = parts[1].split(',') if parts[1] else []
            payload = parts[2] if len(parts) > 2 else ""
            
            # Update discovered sensors
            if sensor_name not in self.discovered_sensors:
                logger.info(f"New sensor discovered: {sensor_name} on pins {pin_list}")
                self.discovered_sensors[sensor_name] = {
                    'pins': pin_list,
                    'last_seen': time.time(),
                    'payload': payload
                }
                # Notify discovery callback
                if self.sensor_discovery_callback:
                    self.sensor_discovery_callback(sensor_name, pin_list, payload)
            else:
                # Update last seen timestamp
                self.discovered_sensors[sensor_name]['last_seen'] = time.time()
                self.discovered_sensors[sensor_name]['payload'] = payload
            
            # Also trigger regular data callback if registered
            if sensor_name in self.callbacks:
                # Parse payload as data
                data_values = [payload]
                self.callbacks[sensor_name](data_values)
                
        except Exception as e:
            logger.error(f"Error parsing header '{header_line}': {e}")
    
    def set_discovery_callback(self, callback):
        """Set callback to be called when new sensor is discovered.
        
        Callback signature: callback(sensor_name: str, pins: list, payload: str)
        """
        self.sensor_discovery_callback = callback
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return list(self.discovered_sensors.keys())
    
    def query_sensors(self):
        """Return currently discovered sensors (passive discovery)."""
        return self.get_discovered_sensors()

    def close(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("Serial connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")

        else:
            logger.info("No active serial connection to close")


# ZCM Communication Implementation
class ZCMCommunication(CommunicationInterface):
    def __init__(self, url, channels):
        super().__init__()
        import zcm
        self.zcm_conn = zcm.ZCM(url)
        if not self.zcm_conn.good():
            print("Error initializing ZCM connection")
            self.zcm_conn = None
        else:
            self.subscriptions = []
            for channel in channels:
                subscription = self.zcm_conn.subscribe(channel, self.message_handler)
                self.subscriptions.append(subscription)
            self.thread = threading.Thread(target=self.zcm_conn.run)
            self.thread.daemon = True
            self.thread.start()

    def message_handler(self, channel, message):
        if channel in self.callbacks:
            data_values = self.parse_message(message)
            self.callbacks[channel](data_values)

    def parse_message(self, message):
        # Implement message parsing based on your ZCM message format
        # For example, if message is a string of comma-separated values:
        data_str = message.decode('utf-8').strip()
        return data_str.split(',')
    
    def query_sensors(self):
        """Query for available sensors (not implemented for ZCM)."""
        logger.warning("Sensor query not implemented for ZCM communication")
        return []

    def close(self):
        if self.zcm_conn:
            self.zcm_conn.stop()
            self.zcm_conn = None
