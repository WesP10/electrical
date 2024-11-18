# sensors/communication.py
import threading
import time
from abc import ABC, abstractmethod
import serial

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
        while self.running:
            try:
                print(f"Attempting to connect to serial port {self.port}")
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                time.sleep(2)  # Wait for Arduino to reset if necessary
                print(f"Connected to serial port {self.port}")
                break  # Exit the loop once connected
            except serial.SerialException as e:
                print(f"Error connecting to serial port {self.port}: {e}")
                print(f"Retrying in {self.reconnect_interval} seconds...")
                time.sleep(self.reconnect_interval)
            except Exception as e:
                print(f"Unexpected error: {e}")
                print(f"Retrying in {self.reconnect_interval} seconds...")
                time.sleep(self.reconnect_interval)

    def read_loop(self):
        self.connect()
        while self.running:
            if self.serial_conn and self.serial_conn.is_open:
                # print("Serial connection is open.")
                try:
                    with self.serial_lock:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        # print(f"Received line: {line}")
                        sensor_id, data_str = self.parse_message(line)
                        if sensor_id and sensor_id in self.callbacks:
                            data_values = data_str.split(',')
                            self.callbacks[sensor_id](data_values)
                except serial.SerialException as e:
                    print(f"SerialException occurred: {e}")
                    print("Closing connection and attempting to reconnect...")
                    with self.serial_lock:
                        try:
                            self.serial_conn.close()
                        except Exception as close_exception:
                            print(f"Error closing serial connection: {close_exception}")
                        self.serial_conn = None
                    self.connect()
                except Exception as e:
                    print(f"Unexpected error during read: {e}")
                    # Close the serial connection and attempt to reconnect
                    with self.serial_lock:
                        if self.serial_conn:
                            try:
                                self.serial_conn.close()
                            except Exception as close_exception:
                                print(f"Error closing serial connection: {close_exception}")
                            self.serial_conn = None
                    self.connect()
            else:
                print("Serial connection is not open. Attempting to reconnect...")
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
                print("Serial connection closed.")
            except Exception as e:
                print(f"Error closing serial connection: {e}")


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
