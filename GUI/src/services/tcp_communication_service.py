"""
TCP Communication Client

This replaces the PySerial communication service with a lightweight TCP client
that connects to the dedicated serial server process. This allows the GUI to
receive serial data without directly accessing the COM port.
"""

import json
import os
import socket
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
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
        logger.info(f"Registered data callback for sensor: {sensor_name}")
        logger.info(f"Total callbacks registered: {list(self.sensor_data_callbacks.keys())}")
    
    def deregister_data_callback(self, sensor_name):
        """Deregister a callback for sensor data."""
        if sensor_name in self.sensor_data_callbacks:
            del self.sensor_data_callbacks[sensor_name]
            logger.debug(f"Deregistered data callback for sensor: {sensor_name}")
    
    def register_callback(self, sensor_id, callback):
        """Register a callback for sensor data (legacy interface for base_sensor.py)."""
        self.sensor_data_callbacks[sensor_id] = callback
        logger.info(f"Registered legacy callback for sensor: {sensor_id}")
        logger.info(f"Total callbacks registered: {list(self.sensor_data_callbacks.keys())}")
    
    def deregister_callback(self, sensor_id):
        """Deregister a callback for sensor data (legacy interface for base_sensor.py)."""
        if sensor_id in self.sensor_data_callbacks:
            del self.sensor_data_callbacks[sensor_id]
            logger.debug(f"Deregistered legacy callback for sensor: {sensor_id}")


class TCPCommunication(BaseCommunication):
    """
    Active TCP-based communication client that requests data from the serial server.
    Uses request-response pattern instead of passive broadcasts.
    This allows GUI hot reload without COM port conflicts.
    """
    
    def __init__(self, server_host='localhost', server_port=9999, reconnect_delay=2.0, poll_interval=0.5):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.reconnect_delay = reconnect_delay
        self.poll_interval = poll_interval  # How often to request data
        
        self.socket = None
        self.running = False
        self.client_thread = None
        self.request_thread = None
        
        # Request tracking
        self.request_id_counter = 0
        self.pending_requests = {}  # {request_id: response_event}
        self.request_lock = threading.Lock()
        
        # Data storage
        self.discovered_sensors = {}  # {sensor_name: {'pins': [], 'last_seen': timestamp}}
        self.connection_status = {'connected': False, 'error': None}
        self.last_data_request = 0  # Timestamp of last data request
        
        logger.info(f"Active TCPCommunication initialized to connect to {server_host}:{server_port}")
        logger.info(f"Data polling interval: {poll_interval}s")
    
    def start(self):
        """Start the TCP client and data requesting threads."""
        if self.running:
            logger.warning("TCP client already running")
            return
        
        self.running = True
        
        # Start client thread for receiving responses
        self.client_thread = threading.Thread(target=self._client_loop, name="TCPClientThread", daemon=True)
        self.client_thread.start()
        
        # Start data request thread for active polling
        self.request_thread = threading.Thread(target=self._request_loop, name="TCPRequestThread", daemon=True)
        self.request_thread.start()
        
        logger.info("Active TCP client threads started")
    
    def stop(self):
        """Stop the TCP client threads."""
        self.running = False
        
        # Clear pending requests
        with self.request_lock:
            for event in self.pending_requests.values():
                event.set()  # Unblock waiting threads
            self.pending_requests.clear()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.client_thread:
            self.client_thread.join(timeout=2.0)
        if self.request_thread:
            self.request_thread.join(timeout=2.0)
            
        logger.info("Active TCP client threads stopped")
    
    def close(self):
        """Close the TCP client connection."""
        self.stop()
        logger.info("TCP client closed")
    
    def _connect_to_server(self):
        """Attempt to connect to the serial server."""
        try:
            logger.info(f"Attempting to connect to serial server at {self.server_host}:{self.server_port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout for connection
            self.socket.connect((self.server_host, self.server_port))
            self.socket.settimeout(None)  # Remove timeout after connection
            
            logger.info(f"Successfully connected to serial server")
            self.connection_status = {'connected': True, 'error': None}
            return True
            
        except socket.error as e:
            logger.warning(f"Failed to connect to serial server: {e}")
            self.connection_status = {'connected': False, 'error': str(e)}
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to serial server: {e}")
            self.connection_status = {'connected': False, 'error': str(e)}
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            return False
    
    def _client_loop(self):
        """Main client loop that handles TCP responses."""
        logger.info("TCP client response loop started")
        
        while self.running:
            # Try to connect if not connected
            if not self.socket:
                if not self._connect_to_server():
                    time.sleep(self.reconnect_delay)
                    continue
            
            try:
                # Receive data from server
                data = self.socket.recv(8192)
                if not data:
                    logger.warning("Server closed connection")
                    self._disconnect()
                    continue
                
                # Decode and process messages
                messages = data.decode('utf-8').strip().split('\n')
                for message_str in messages:
                    if message_str:
                        try:
                            message = json.loads(message_str)
                            self._process_server_response(message)
                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse JSON response: {message_str} - {e}")
                
            except socket.error as e:
                logger.warning(f"TCP client error: {e}")
                self._disconnect()
                time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error in client loop: {e}")
                time.sleep(0.1)
        
        logger.info("TCP client response loop stopped")
    
    def _request_loop(self):
        """Active loop that periodically requests data from server."""
        logger.info("TCP data request loop started")
        
        while self.running:
            try:
                if self.socket and self.connection_status['connected']:
                    # Request data from the last poll interval
                    current_time = time.time()
                    from_time = max(self.last_data_request, current_time - self.poll_interval * 1.5)  # Small overlap
                    
                    self._request_data(from_time, current_time)
                    self.last_data_request = current_time
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in request loop: {e}")
                time.sleep(self.poll_interval)
        
        logger.info("TCP data request loop stopped")
    
    def _disconnect(self):
        """Handle disconnection from server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connection_status = {'connected': False, 'error': 'Disconnected'}
        logger.info("Disconnected from serial server")
    
    def _send_request(self, request_data, timeout=5.0):
        """Send a request to the server and wait for response."""
        if not self.socket or not self.connection_status['connected']:
            logger.warning("Cannot send request: not connected to server")
            return None
        
        # Generate request ID
        with self.request_lock:
            self.request_id_counter += 1
            request_id = self.request_id_counter
            request_data['request_id'] = request_id
            
            # Create event to wait for response
            response_event = threading.Event()
            self.pending_requests[request_id] = {
                'event': response_event,
                'response': None
            }
        
        try:
            # Send request
            request_json = json.dumps(request_data) + '\n'
            self.socket.send(request_json.encode('utf-8'))
            
            # Wait for response
            if response_event.wait(timeout):
                with self.request_lock:
                    response_data = self.pending_requests[request_id]['response']
                    del self.pending_requests[request_id]
                return response_data
            else:
                logger.warning(f"Request {request_id} timed out")
                with self.request_lock:
                    if request_id in self.pending_requests:
                        del self.pending_requests[request_id]
                return None
                
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            with self.request_lock:
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
            return None
    
    def _request_data(self, from_time, to_time):
        """Request data from server within time range (or just send heartbeat with periodic updates)."""
        # With periodic updates, we primarily rely on server pushing data
        # But we can still support explicit requests when needed
        request = {
            'type': 'get_data',
            'from_time': from_time,
            'to_time': to_time,
            'data_types': ['discovery', 'sensor_data']
        }
        
        logger.debug(f"📤 Requesting data from {from_time:.2f} to {to_time:.2f}")
        try:
            response = self._send_request(request, timeout=1.0)  # Shorter timeout since we have periodic updates
            if response and response.get('type') == 'data_response':
                logger.debug(f"📥 Received data response with {len(response.get('data', []))} entries")
                self._process_data_response(response)
            else:
                logger.debug(f"No explicit data response (relying on periodic updates)")
        except Exception as e:
            logger.debug(f"Request failed, relying on periodic updates: {e}")
    
    def _process_server_response(self, message):
        """Process a response received from the serial server."""
        try:
            message_type = message.get('type')
            logger.debug(f"Received server response: {message_type}")
            
            if message_type == 'periodic_update':
                # Handle periodic data updates from server
                logger.debug(f"📥 Received periodic update with {len(message.get('data', []))} entries")
                self._process_data_response(message)
            elif message_type == 'data_response':
                logger.debug(f"📥 Received data_response with {len(message.get('data', []))} entries")
                self._process_data_response(message)
            elif message_type == 'status_response':
                self._process_status_response(message)
            elif message_type == 'error_response':
                self._process_error_response(message)
            elif message_type == 'server_status':
                self._handle_server_status(message)
            else:
                # Handle responses with request_id
                request_id = message.get('request_id')
                if request_id:
                    with self.request_lock:
                        if request_id in self.pending_requests:
                            self.pending_requests[request_id]['response'] = message
                            self.pending_requests[request_id]['event'].set()
                            logger.info(f"Matched request {request_id} with response")
                            return
                
                logger.debug(f"Unknown response type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing server response {message}: {e}")
    
    def _process_data_response(self, response):
        """Process data response from server."""
        try:
            data_entries = response.get('data', [])
            logger.info(f"Processing data response with {len(data_entries)} entries")
            
            for entry in data_entries:
                entry_type = entry.get('type')
                logger.debug(f"Processing entry type: {entry_type}")
                
                if entry_type == 'discovery':
                    logger.info(f"Processing discovery entry: {entry.get('sensor_name', 'Unknown')}")
                    self._handle_sensor_discovery(entry)
                elif entry_type == 'sensor_data':
                    logger.info(f"Processing sensor data entry: {entry.get('sensor_name', 'Unknown')} = {entry.get('values', 'N/A')}")
                    self._handle_sensor_data(entry)
                
        except Exception as e:
            logger.error(f"Error processing data response: {e}")
    
    def _process_status_response(self, response):
        """Process status response from server."""
        try:
            logger.info(f"Server status: {response}")
        except Exception as e:
            logger.error(f"Error processing status response: {e}")
    
    def _process_error_response(self, response):
        """Process error response from server."""
        try:
            error = response.get('error', 'Unknown error')
            logger.error(f"Server error response: {error}")
        except Exception as e:
            logger.error(f"Error processing error response: {e}")
    
    def _handle_sensor_discovery(self, entry):
        """Handle sensor discovery entry from server."""
        try:
            sensor_name = entry['sensor_name']
            pins = entry['pins']
            payload = entry['payload']
            timestamp = entry['timestamp']
            
            # Update discovered sensors
            is_new = sensor_name not in self.discovered_sensors
            self.discovered_sensors[sensor_name] = {
                'pins': pins,
                'last_seen': timestamp,
                'last_payload': payload
            }
            
            if is_new:
                logger.info(f"New sensor discovered via TCP: '{sensor_name}' on pins {pins}")
                
                # Call discovery callback for new sensors only
                if self.sensor_discovery_callback:
                    self.sensor_discovery_callback(sensor_name, pins, payload)
                
        except Exception as e:
            logger.error(f"Error handling sensor discovery: {e}")
    
    def _handle_sensor_data(self, entry):
        """Handle sensor data entry from server."""
        try:
            sensor_name = entry['sensor_name']
            values = entry['values']
            timestamp = entry['timestamp']
            
            # Update last seen time
            if sensor_name in self.discovered_sensors:
                self.discovered_sensors[sensor_name]['last_seen'] = timestamp
            
            # Call data callback if registered
            if sensor_name in self.sensor_data_callbacks:
                logger.info(f"Calling callback for {sensor_name} with values {values}")
                self.sensor_data_callbacks[sensor_name](values)
            else:
                logger.debug(f"No callback registered for sensor: {sensor_name}")
                
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    def _handle_server_status(self, message):
        """Handle server status message."""
        try:
            serial_connected = message['serial_connected']
            discovered_sensors = message['discovered_sensors']
            buffer_size = message['buffer_size']
            
            logger.info(f"Server status - Serial: {'Connected' if serial_connected else 'Disconnected'}, "
                       f"Sensors: {discovered_sensors}, Buffer: {buffer_size}")
            
            # Update our discovered sensors list
            for sensor_name in discovered_sensors:
                if sensor_name not in self.discovered_sensors:
                    self.discovered_sensors[sensor_name] = {
                        'pins': [],
                        'last_seen': time.time(),
                        'last_payload': ''
                    }
                    
        except Exception as e:
            logger.error(f"Error handling server status: {e}")
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return list(self.discovered_sensors.keys())
    
    def get_buffer_lines(self, n=10):
        """Get the last n raw lines from the buffer."""
        return [item['line'] for item in self.raw_lines[-n:]]
    
    def is_connected_to_server(self):
        """Check if connected to the serial server."""
        return self.socket is not None and self.connection_status['connected']
    
    def get_connection_status(self):
        """Get current connection status."""
        return self.connection_status
    
    def has_recent_data_for_sensor(self, sensor_name: str) -> bool:
        """Check if sensor has recent data or is actively sending data."""
        logger.info(f"Checking recent data for sensor: {sensor_name}")
        logger.info(f"Discovered sensors: {list(self.discovered_sensors.keys())}")
        
        # First check if sensor was ever discovered
        if sensor_name not in self.discovered_sensors:
            logger.info(f"Sensor {sensor_name} not in discovered sensors")
            return False
        
        current_time = time.time()
        last_seen = self.discovered_sensors[sensor_name]['last_seen']
        time_diff = current_time - last_seen
        
        # Use shorter timeout for faster disconnection detection
        discovery_timeout = 10.0  # Reduced from 30 seconds
        recent_discovery = time_diff < discovery_timeout
        
        logger.info(f"Sensor {sensor_name}: last_seen={last_seen}, current={current_time}, diff={time_diff:.2f}s")
        logger.info(f"Discovery recent: {recent_discovery} (timeout: {discovery_timeout}s)")
        
        if recent_discovery:
            logger.info(f"Sensor {sensor_name} has recent discovery data")
            return True
        else:
            logger.info(f"Sensor {sensor_name} discovery data is old")
            # Mark as unavailable after timeout
            return False
    
    def get_sensor_data_dataframe(self, sensor_name: str):
        """Get recent sensor data as pandas DataFrame."""
        try:
            import pandas as pd
            import datetime
            
            # Check if sensor has recent data
            if not self.has_recent_data_for_sensor(sensor_name):
                return pd.DataFrame()
            
            # Create mock recent data points based on sensor activity
            now = datetime.datetime.now()
            timestamps = [now - datetime.timedelta(seconds=i*2) for i in range(15, 0, -1)]
            
            # Create simple mock data
            data_points = []
            for ts in timestamps:
                data_points.append({
                    'Time': ts,
                    'value': 4.0  # Mock value - in real implementation would come from stored data
                })
            
            return pd.DataFrame(data_points)
                
        except Exception as e:
            logger.error(f"Error getting sensor data for {sensor_name}: {e}")
            return pd.DataFrame()


class CommunicationService:
    """
    High-level communication service that manages TCP or mock communication.
    This is the main interface used by the application.
    """
    
    def __init__(self, config):
        """
        Initialize the communication service.
        
        Args:
            config: CommunicationConfig object with settings
        """
        self.config = config
        self.comm = None
        
        # Choose implementation based on config and environment
        # Check if serial server mode is enabled (indicates we should use TCP)
        serial_server_mode = os.environ.get('SERIAL_SERVER_MODE', 'false').lower() == 'true'
        
        if serial_server_mode and not config.use_mock:
            logger.info("Using TCPCommunication to connect to serial server")
            # Check if serial server is actually running
            try:
                import socket
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = test_socket.connect_ex(('localhost', 9999))
                test_socket.close()
                if result == 0:
                    logger.info("Serial server detected on port 9999, using TCP communication")
                    self.comm = TCPCommunication(
                        server_host='localhost',
                        server_port=9999,
                        reconnect_delay=2.0
                    )
                else:
                    logger.warning("SERIAL_SERVER_MODE enabled but no server found on port 9999, falling back to mock")
                    from sensors.mock_communication import MockCommunication
                    self.comm = MockCommunication()
            except Exception as e:
                logger.error(f"Error checking for serial server: {e}, using mock communication")
                from sensors.mock_communication import MockCommunication
                self.comm = MockCommunication()
        elif config.use_mock or config.port == 'loop://' or config.port.startswith('mock'):
            logger.info("Using MockCommunication (simulated sensor data)")
            from sensors.mock_communication import MockCommunication
            self.comm = MockCommunication()
        else:
            logger.info("Using TCPCommunication to connect to serial server")
            # For TCP communication, we connect to the serial server
            # The serial server should already be running and connected to the actual serial port
            self.comm = TCPCommunication(
                server_host='localhost',
                server_port=9999,  # Default port for serial server
                reconnect_delay=2.0
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
    
    def register_callback(self, sensor_id, callback):
        """Register callback for sensor data (legacy interface)."""
        return self.comm.register_callback(sensor_id, callback)
    
    def deregister_callback(self, sensor_id):
        """Deregister callback for sensor data (legacy interface)."""
        return self.comm.deregister_callback(sensor_id)
    
    def get_discovered_sensors(self):
        """Get list of discovered sensor names."""
        return self.comm.get_discovered_sensors()
    
    def get_buffer_lines(self, n=10):
        """Get the last n lines from the buffer."""
        return self.comm.get_buffer_lines(n)
    
    def is_connected_to_server(self):
        """Check if connected to the serial server (TCP only)."""
        if hasattr(self.comm, 'is_connected_to_server'):
            return self.comm.is_connected_to_server()
        return True  # Mock communication is always "connected"
    
    def get_connection_status(self):
        """Get current connection status."""
        if hasattr(self.comm, 'get_connection_status'):
            return self.comm.get_connection_status()
        return {'connected': True, 'error': None}  # Mock communication status
    
    def has_recent_data_for_sensor(self, sensor_name: str) -> bool:
        """Check if sensor has recent data (within last 5 seconds)."""
        if hasattr(self.comm, 'has_recent_data_for_sensor'):
            return self.comm.has_recent_data_for_sensor(sensor_name)
        return False
    
    def get_sensor_data_dataframe(self, sensor_name: str):
        """Get recent sensor data as pandas DataFrame."""
        if hasattr(self.comm, 'get_sensor_data_dataframe'):
            return self.comm.get_sensor_data_dataframe(sensor_name)
        return None
    
    def close(self):
        """Close and cleanup the communication service."""
        if self.comm:
            self.comm.close()
            logger.info("Communication service closed")
    
    def switch_to_mock_mode(self) -> bool:
        """Switch to mock communication mode."""
        try:
            logger.info("Switching communication service to mock mode")
            
            # Stop current communication
            if self.comm:
                self.comm.stop()
                self.comm.close()
            
            # Create new mock communication
            from sensors.mock_communication import MockCommunication
            self.comm = MockCommunication()
            self.comm.start()
            
            # Update config to reflect new mode
            self.config.use_mock = True
            self.config.port = 'mock://'
            
            logger.info("Successfully switched to mock communication mode")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to mock mode: {e}")
            return False
    
    def switch_to_hardware_mode(self, port: str, baud_rate: int) -> bool:
        """Switch to hardware communication mode with specified port and baud rate."""
        try:
            logger.info(f"Switching communication service to hardware mode: {port} at {baud_rate} baud")
            
            # Stop current communication
            if self.comm:
                self.comm.stop() 
                self.comm.close()
            
            # Create new TCP communication to serial server
            self.comm = TCPCommunication(
                server_host='localhost',
                server_port=9999,
                reconnect_delay=2.0
            )
            self.comm.start()
            
            # Update config to reflect new mode
            self.config.use_mock = False
            self.config.port = port
            self.config.baudrate = baud_rate
            
            # Send reconfiguration message to serial server
            success = self._reconfigure_serial_server(port, baud_rate)
            
            if success:
                logger.info(f"Successfully switched to hardware mode: {port} at {baud_rate} baud")
                return True
            else:
                logger.warning("Hardware mode switch partially successful - server reconfiguration pending")
                # Even if reconfiguration fails initially, the TCP connection might work
                # Let's check if we can at least connect to the server
                if self.is_connected_to_server():
                    logger.info("TCP connection established, hardware mode switch considered successful")
                    return True
                else:
                    logger.error("Failed to establish TCP connection to serial server")
                    return False
                
        except Exception as e:
            logger.error(f"Error switching to hardware mode: {e}")
            return False
    
    def _reconfigure_serial_server(self, port: str, baud_rate: int) -> bool:
        """Send reconfiguration request to serial server."""
        try:
            if hasattr(self.comm, '_send_request'):
                request = {
                    'type': 'reconfigure_connection',
                    'port': port,
                    'baud_rate': baud_rate
                }
                response = self.comm._send_request(request, timeout=10.0)
                if response and response.get('type') == 'reconfigure_response':
                    return response.get('success', False)
            return False
        except Exception as e:
            logger.error(f"Error reconfiguring serial server: {e}")
            return False
    
    def get_current_mode(self) -> Dict:
        """Get current communication mode and settings."""
        # Determine if we're in mock mode based on actual communication type
        is_mock = False
        if self.comm:
            comm_type = type(self.comm).__name__
            is_mock = comm_type == 'MockCommunication'
        
        mode_info = {
            'is_mock': is_mock,
            'port': getattr(self.config, 'port', 'unknown'),
            'baud_rate': getattr(self.config, 'baudrate', 115200),
            'connected': self.is_connected_to_server()
        }
        
        if hasattr(self.comm, 'get_connection_status'):
            status = self.comm.get_connection_status()
            mode_info.update(status)
        
        return mode_info
    
    def clear_discovered_sensors(self) -> None:
        """Clear all discovered sensors (used when switching microcontrollers)."""
        if hasattr(self.comm, 'discovered_sensors'):
            self.comm.discovered_sensors.clear()
            logger.info("Cleared discovered sensors for microcontroller switch")