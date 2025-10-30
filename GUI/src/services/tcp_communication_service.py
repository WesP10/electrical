"""
TCP Communication Service

Direct TCP client that connects to the dedicated serial server process. 
This allows the GUI to receive serial data without directly accessing the COM port.

No mock modes, no abstractions - just a clean TCP client implementation.
"""

import json
import os
import socket
import threading
import time
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)


class CommunicationService:
    """
    TCP-based communication client that requests data from the serial server.
    Uses request-response pattern instead of passive broadcasts.
    This allows GUI hot reload without COM port conflicts.
    """
    
    def __init__(self, config=None, server_host=None, server_port=None, reconnect_delay=2.0, poll_interval=0.5):
        """
        Initialize the communication service.
        
        Args:
            config: CommunicationConfig object (optional, uses env vars if not provided)
            server_host: Override server host (defaults to env SERIAL_SERVER_HOST)
            server_port: Override server port (defaults to env SERIAL_SERVER_PORT)
            reconnect_delay: Delay between reconnection attempts
            poll_interval: How often to request data
        """
        self.config = config
        
        # Get configuration from environment or parameters
        self.server_host = server_host or os.environ.get('SERIAL_SERVER_HOST', 'localhost')
        # Get configuration from environment or parameters
        self.server_host = server_host or os.environ.get('SERIAL_SERVER_HOST', 'localhost')
        self.server_port = server_port or int(os.environ.get('SERIAL_SERVER_PORT', '9999'))
        self.reconnect_delay = reconnect_delay
        self.poll_interval = poll_interval  # How often to request data
        
        # Callbacks
        self.sensor_discovery_callback = None
        self.sensor_data_callbacks = {}  # {sensor_name: callback_function}
        
        self.socket = None
        self.running = False
        self.client_thread = None
        self.request_thread = None
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
        
        # Sensor data buffer (stores recent readings for each sensor)
        self.sensor_data_buffer = {}  # {sensor_name: [(timestamp, values), ...]}
        self.max_data_points = 100  # Keep last 100 data points per sensor
        self.data_buffer_lock = threading.Lock()
        
        # Console message buffer for debugging (stores last 100 messages)
        self.console_messages = []  # List of {timestamp, direction, message} dicts
        self.max_console_messages = 100
        self.console_lock = threading.Lock()
        
        logger.info(f"TCP Communication initialized to connect to {self.server_host}:{self.server_port}")
        logger.info(f"Data polling interval: {self.poll_interval}s")
        
        # Auto-start the service
        self.start()
    
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
            self._log_console_message('info', f"Connecting to {self.server_host}:{self.server_port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout for connection
            self.socket.connect((self.server_host, self.server_port))
            self.socket.settimeout(None)  # Remove timeout after connection
            
            logger.info(f"Successfully connected to serial server")
            self._log_console_message('info', f"Connected to serial server")
            self.connection_status = {'connected': True, 'error': None}
            return True
            
        except socket.error as e:
            logger.warning(f"Failed to connect to serial server: {e}")
            self._log_console_message('error', f"Connection failed: {e}")
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
            self._log_console_message('error', f"Unexpected error: {e}")
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
                    self._log_console_message('error', "Server closed connection")
                    self._disconnect()
                    continue
                
                # Decode and process messages
                messages = data.decode('utf-8').strip().split('\n')
                for message_str in messages:
                    if message_str:
                        try:
                            # Log received message
                            self._log_console_message('received', message_str)
                            message = json.loads(message_str)
                            self._process_server_response(message)
                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse JSON response: {message_str} - {e}")
                            self._log_console_message('error', f"Invalid JSON: {message_str[:100]}...")
                
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
            self._log_console_message('sent', request_json.strip())
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
            
            # Store sensor data in buffer
            with self.data_buffer_lock:
                if sensor_name not in self.sensor_data_buffer:
                    self.sensor_data_buffer[sensor_name] = []
                
                # Add new data point
                self.sensor_data_buffer[sensor_name].append({
                    'timestamp': timestamp,
                    'values': values
                })
                
                # Keep only the last max_data_points
                if len(self.sensor_data_buffer[sensor_name]) > self.max_data_points:
                    self.sensor_data_buffer[sensor_name] = self.sensor_data_buffer[sensor_name][-self.max_data_points:]
            
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
    
    def get_console_messages(self, n=50):
        """Get the last n console messages for display."""
        with self.console_lock:
            return self.console_messages[-n:] if self.console_messages else []
    
    def _log_console_message(self, direction: str, message: str):
        """Log a message to the console buffer."""
        import datetime
        with self.console_lock:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.console_messages.append({
                'timestamp': timestamp,
                'direction': direction,  # 'sent', 'received', 'info', 'error'
                'message': message
            })
            # Keep only the last max_console_messages
            if len(self.console_messages) > self.max_console_messages:
                self.console_messages = self.console_messages[-self.max_console_messages:]
    
    def get_buffer_lines(self, n=10):
        """Get the last n raw lines from the buffer."""
        return [item['line'] for item in self.raw_lines[-n:]]
    
    def is_connected_to_server(self):
        """Check if connected to the serial server."""
        return self.socket is not None and self.connection_status['connected']
    
    def is_connected(self):
        """Alias for is_connected_to_server() for backward compatibility."""
        return self.is_connected_to_server()
    
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
            
            # Get data from buffer
            with self.data_buffer_lock:
                if sensor_name not in self.sensor_data_buffer or not self.sensor_data_buffer[sensor_name]:
                    logger.debug(f"No buffered data for {sensor_name}")
                    return pd.DataFrame()
                
                # Convert buffer data to DataFrame
                data_points = []
                for entry in self.sensor_data_buffer[sensor_name]:
                    timestamp = entry['timestamp']
                    values = entry['values']
                    
                    # Convert timestamp to datetime
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    
                    # Create data point with all values
                    data_point = {'Time': dt}
                    
                    # Add each value from the values array
                    # Most sensors have one value, but some may have multiple (e.g., accelerometer: x, y, z)
                    if len(values) == 1:
                        data_point['value'] = values[0]
                    else:
                        for i, val in enumerate(values):
                            data_point[f'value_{i}'] = val
                    
                    data_points.append(data_point)
                
                logger.info(f"Returning {len(data_points)} real data points for {sensor_name}")
                return pd.DataFrame(data_points)
                
        except Exception as e:
            logger.error(f"Error getting sensor data for {sensor_name}: {e}")
            return pd.DataFrame()
    
    def clear_discovered_sensors(self) -> None:
        """Clear all discovered sensors (used when switching microcontrollers)."""
        self.discovered_sensors.clear()
        logger.info("Cleared discovered sensors for microcontroller switch")
    
    def switch_to_hardware_mode(self, port: str, baud_rate: int) -> bool:
        """
        Switch to hardware communication mode with specified port and baud rate.
        
        Note: This sends a reconfiguration request to the serial server.
        The serial server must support dynamic reconfiguration for this to work.
        """
        try:
            logger.info(f"Requesting serial server to switch to: {port} at {baud_rate} baud")
            
            # Send reconfiguration message to serial server
            request = {
                'type': 'reconfigure_connection',
                'port': port,
                'baud_rate': baud_rate
            }
            response = self._send_request(request, timeout=10.0)
            
            if response and response.get('type') == 'reconfigure_response':
                success = response.get('success', False)
                if success:
                    logger.info(f"Successfully reconfigured serial server to {port} at {baud_rate} baud")
                    # Clear discovered sensors when switching hardware
                    self.clear_discovered_sensors()
                    return True
                else:
                    error = response.get('error', 'Unknown error')
                    logger.error(f"Failed to reconfigure serial server: {error}")
                    return False
            else:
                logger.warning("No response from serial server for reconfiguration request")
                return False
                
        except Exception as e:
            logger.error(f"Error switching to hardware mode: {e}")
            return False
    
    def get_current_mode(self) -> Dict:
        """Get current communication mode and settings from the serial server."""
        mode_info = {
            'is_mock': False,  # We're always in TCP mode now
            'connected': self.is_connected_to_server()
        }
        
        # Try to get additional status from server
        if self.is_connected_to_server():
            try:
                request = {'type': 'get_status'}
                response = self._send_request(request, timeout=2.0)
                if response and response.get('type') == 'status_response':
                    mode_info['port'] = response.get('serial_port', 'unknown')
                    mode_info['baud_rate'] = response.get('baud_rate', 115200)
                    mode_info['serial_connected'] = response.get('serial_connected', False)
            except Exception as e:
                logger.debug(f"Could not get status from server: {e}")
        
        return mode_info
