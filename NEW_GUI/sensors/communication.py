import threading
from abc import ABC, abstractmethod

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

# PySerial Communication Implementation
class PySerialCommunication(CommunicationInterface):
    def __init__(self, port, baudrate=9600, timeout=1):
        super().__init__()
        import serial
        try:
            self.serial_conn = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            self.running = True
            self.thread = threading.Thread(target=self.read_loop)
            self.thread.daemon = True
            self.thread.start()
        except serial.SerialException as e:
            print(f"Error initializing serial connection: {e}")
            self.serial_conn = None

    def read_loop(self):
        while self.running and self.serial_conn and self.serial_conn.is_open:
            line = self.serial_conn.readline().decode('utf-8').strip()
            if line:
                sensor_id, data_str = self.parse_message(line)
                if sensor_id and sensor_id in self.callbacks:
                    data_values = data_str.split(',')
                    self.callbacks[sensor_id](data_values)

    def parse_message(self, message):
        parts = message.split(':', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        else:
            return None, None

    def close(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

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
