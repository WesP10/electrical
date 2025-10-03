# sensors/communication.py
import threading
import time
from abc import ABC, abstractmethod
import serial
import sys
from pathlib import Path

# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
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
        self.thread = threading.Thread(target=self.read_loop, name="SerialReadThread")
        self.thread.daemon = True
        self.thread.start()

    def connect(self):
        # Check if this is a mock port (no real hardware)
        if self.port == 'loop://' or self.port.startswith('mock'):
            logger.info(f"[MOCK MODE] Using mock communication - no hardware connection needed")
            logger.info(f"[MOCK MODE] Port configured as: {self.port}")
            self.serial_conn = None  # No real connection for mock mode
            return
        
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
                    logger.error(f"[ERROR] Failed to connect after {max_retries} attempts. Switching to mock mode.")
                    logger.info(f"[MOCK MODE] No microcontroller detected - using simulated data")
                    self.port = 'mock://fallback'  # Mark as mock mode
                    self.serial_conn = None
                    break
            except Exception as e:
                retry_count += 1
                logger.error(f"[ERROR] Unexpected error: {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying in {self.reconnect_interval} seconds... ({retry_count}/{max_retries})")
                    time.sleep(self.reconnect_interval)
                else:
                    logger.error(f"[ERROR] Failed to connect after {max_retries} attempts. Switching to mock mode.")
                    logger.info(f"[MOCK MODE] Hardware connection failed - using simulated data")
                    self.port = 'mock://fallback'  # Mark as mock mode
                    self.serial_conn = None
                    break

    def read_loop(self):
        self.connect()
        
        # If we're in mock mode, don't try to read from serial
        if self.port.startswith('mock') or self.port == 'loop://':
            logger.info("[MOCK MODE] Mock communication active - no serial reading needed")
            logger.info("[MOCK MODE] Real sensor data will be provided by MockCommunication service")
            while self.running:
                time.sleep(1)  # Just sleep in mock mode
            return
        
        while self.running:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    with self.serial_lock:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        logger.debug(f"Received line: {line}")
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
                if not self.port.startswith('mock'):
                    logger.debug("Serial connection is not open. Attempting to reconnect...")
                    self.connect()
            time.sleep(0.1)  # Small delay to prevent a tight loop

    def parse_message(self, message):
        parts = message.split(':', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        else:
            return None, None

    def close(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("Serial connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")
        elif self.port.startswith('mock') or self.port == 'loop://':
            logger.info("[MOCK MODE] Mock communication closed - no hardware to disconnect")
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

    def close(self):
        if self.zcm_conn:
            self.zcm_conn.stop()
            self.zcm_conn = None
