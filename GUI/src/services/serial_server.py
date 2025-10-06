#!/usr/bin/env python3
"""
Standalone Serial Communication Server

This server runs as a separate process and handles all PySerial communication.
It provides a TCP interface for the GUI to connect and receive sensor data.

Key features:
- Dedicated process for PySerial (no conflicts from GUI hot reload)
- TCP server for multiple GUI clients to connect
- JSON-based protocol for sensor discovery and data streaming
- Automatic Arduino detection and connection
- Comprehensive logging of serial communication
"""

import json
import socket
import threading
import time
import signal
import sys
import argparse
from pathlib import Path
from collections import deque, defaultdict
import logging
from typing import Dict, List, Optional, Tuple

# Import pyserial explicitly to avoid naming conflicts
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('serial_server.log')
    ]
)
logger = logging.getLogger(__name__)


class SerialCommunicationServer:
    """
    Passive serial communication server that buffers PySerial data.
    Provides TCP interface for GUI clients to request data from specific time ranges.
    
    Key Features:
    - Passive buffering of serial data (no active broadcasting)
    - Time-based data storage (last 5 seconds only)
    - Request-response TCP protocol for data retrieval
    - Hot reload friendly (GUI requests data when needed)
    """
    
    DATA_RETENTION_SECONDS = 5.0  # Keep only last 5 seconds of data
    
    def __init__(self, port, baudrate=115200, tcp_port=9999):
        self.serial_port = port
        self.baudrate = baudrate
        self.tcp_port = tcp_port
        
        # Serial connection
        self.serial_conn = None
        self.serial_running = False
        self.serial_thread = None
        
        # TCP server
        self.tcp_server = None
        self.tcp_running = False
        self.tcp_thread = None
        
        # Time-based data buffer - stores (timestamp, data_type, content)
        self.data_buffer = deque()  # [(timestamp, 'discovery'|'data', content)]
        self.buffer_lock = threading.RLock()  # Thread-safe access to buffer
        
        # Quick sensor tracking
        self.discovered_sensors = {}  # {sensor_name: {'pins': [], 'last_seen': timestamp}}
        self.connected_clients = []  # List of client connections
        
        # Cleanup thread for old data
        self.cleanup_running = False
        self.cleanup_thread = None
        
        # Statistics
        self.lines_read_count = 0
        self.bytes_read_count = 0
        self.last_status_log = time.time()
        
        logger.info(f"Passive serial server initialized for port {port} at {baudrate} baud")
        logger.info(f"TCP server will listen on port {tcp_port}")
        logger.info(f"Data retention: {self.DATA_RETENTION_SECONDS} seconds")
    
    def start(self):
        """Start serial communication, TCP server, and cleanup thread."""
        logger.info("Starting Passive Serial Communication Server...")
        
        # Start buffer cleanup thread
        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, name="CleanupThread", daemon=True)
        self.cleanup_thread.start()
        
        # Start serial communication
        self.serial_running = True
        self.serial_thread = threading.Thread(target=self._serial_loop, name="SerialThread", daemon=True)
        self.serial_thread.start()
        
        # Start TCP server
        self.tcp_running = True
        self.tcp_thread = threading.Thread(target=self._tcp_server_loop, name="TCPServerThread", daemon=True)
        self.tcp_thread.start()
        
        logger.info("Passive Serial Communication Server started successfully")
    
    def stop(self):
        """Stop all communication and cleanup."""
        logger.info("Stopping Passive Serial Communication Server...")
        
        # Stop cleanup thread
        self.cleanup_running = False
        
        # Stop TCP server
        self.tcp_running = False
        if self.tcp_server:
            try:
                self.tcp_server.close()
            except:
                pass
        
        # Close all client connections
        for client in self.connected_clients[:]:
            try:
                client.close()
            except:
                pass
        self.connected_clients.clear()
        
        # Stop serial communication
        self.serial_running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except:
                pass
        
        # Wait for threads to finish
        if self.tcp_thread:
            self.tcp_thread.join(timeout=2.0)
        if self.serial_thread:
            self.serial_thread.join(timeout=2.0)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2.0)
        
        logger.info("Passive Serial Communication Server stopped")
    
    def _connect_serial(self):
        """Connect to the serial port."""
        try:
            logger.info(f"Attempting to connect to serial port {self.serial_port} at {self.baudrate} baud")
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baudrate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                exclusive=True  # Exclusive access to prevent conflicts
            )
            # Wait for Arduino to reset
            time.sleep(2)
            # Clear startup noise
            self.serial_conn.reset_input_buffer()
            logger.info(f"Successfully connected to {self.serial_port}")
            
            # Log connection status
            logger.info(f"Connected to {self.serial_port} at {self.baudrate} baud")
            self._broadcast_to_clients({
                'type': 'connection_status',
                'connected': True,
                'port': self.serial_port,
                'baudrate': self.baudrate
            })
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to serial port {self.serial_port}: {e}")
            self.serial_conn = None
            # Notify clients about connection failure
            self._broadcast_to_clients({
                'type': 'connection_status',
                'connected': False,
                'error': str(e)
            })
        except Exception as e:
            logger.error(f"Unexpected error connecting to serial: {e}")
            self.serial_conn = None
    
    def _serial_loop(self):
        """Main serial reading loop."""
        logger.info("Serial read loop started")
        
        while self.serial_running:
            # Check if connected
            if not self.serial_conn or not self.serial_conn.is_open:
                logger.warning("Serial connection lost, attempting to reconnect...")
                time.sleep(2)
                self._connect_serial()
                continue
            
            try:
                # Read until newline character
                line_bytes = self.serial_conn.read_until(b'\n')
                
                if line_bytes:
                    self.bytes_read_count += len(line_bytes)
                    logger.debug(f"Raw bytes received ({len(line_bytes)} bytes): {line_bytes}")
                
                    try:
                        # Decode and strip whitespace
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                        
                        # Log every line received
                        logger.info(f"Serial line received: '{line}'")
                        self.lines_read_count += 1
                        
                        if line:
                            # Process the line
                            self._process_serial_line(line)
                        else:
                            logger.debug("Received empty line (after stripping)")
                            
                    except UnicodeDecodeError as e:
                        logger.warning(f"Decode error on line {line_bytes}: {e}")
                        continue
                else:
                    logger.debug("No data received (timeout)")
                
                # Periodic status logging
                current_time = time.time()
                if current_time - self.last_status_log > 30:
                    self._log_status()
                    self.last_status_log = current_time
                        
            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error in serial loop: {e}")
                time.sleep(0.1)
        
        logger.info("Serial read loop stopped")
    
    def _process_serial_line(self, line):
        """Process a line from serial and store in time-based buffer."""
        try:
            current_time = time.time()
            
            # Store raw line in buffer
            with self.buffer_lock:
                self.data_buffer.append((current_time, 'raw_line', {'line': line}))
            
            # Check if it's a header message
            if line.startswith('*H*_'):
                # Parse header and store discovery
                sensor_info = self._parse_header(line)
                if sensor_info:
                    discovery_data = {
                        'sensor_name': sensor_info['name'],
                        'pins': sensor_info['pins'],
                        'payload': sensor_info['payload']
                    }
                    
                    with self.buffer_lock:
                        self.data_buffer.append((current_time, 'discovery', discovery_data))
                    
                    # Also process sensor data from header payload
                    data_info = self._parse_data(sensor_info['payload'])
                    if data_info:
                        sensor_data = {
                            'sensor_name': sensor_info['name'],
                            'values': data_info['values']
                        }
                        with self.buffer_lock:
                            self.data_buffer.append((current_time, 'sensor_data', sensor_data))
                    else:
                        # Parse the payload directly since it's in format "measurement:value"
                        if ':' in sensor_info['payload']:
                            measurement_parts = sensor_info['payload'].split(',')
                            parsed_values = []
                            for part in measurement_parts:
                                if ':' in part:
                                    key, value = part.split(':', 1)
                                    parsed_values.append(f"{key.strip()}:{value.strip()}")
                            
                            if parsed_values:
                                sensor_data = {
                                    'sensor_name': sensor_info['name'],
                                    'values': parsed_values
                                }
                                with self.buffer_lock:
                                    self.data_buffer.append((current_time, 'sensor_data', sensor_data))
            else:
                # Regular data message
                data_info = self._parse_data(line)
                if data_info:
                    sensor_data = {
                        'sensor_name': data_info['name'],
                        'values': data_info['values']
                    }
                    with self.buffer_lock:
                        self.data_buffer.append((current_time, 'sensor_data', sensor_data))
                
        except Exception as e:
            logger.debug(f"Error processing line '{line}': {e}")
    
    def _cleanup_loop(self):
        """Background thread to clean up old data from buffer."""
        logger.info("Starting data cleanup thread")
        
        while self.cleanup_running:
            try:
                current_time = time.time()
                cutoff_time = current_time - self.DATA_RETENTION_SECONDS
                
                with self.buffer_lock:
                    # Remove old entries from the beginning
                    while self.data_buffer and self.data_buffer[0][0] < cutoff_time:
                        self.data_buffer.popleft()
                
                # Sleep for a bit before next cleanup
                time.sleep(0.5)  # Cleanup every 500ms
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(1.0)
        
        logger.info("Data cleanup thread stopped")
    
    def _parse_header(self, header_line):
        """Parse header format and return sensor info."""
        try:
            # Remove *H*_ prefix
            content = header_line[4:]
            parts = content.split('_', 2)
            
            if len(parts) < 3:
                logger.warning(f"Invalid header format: {header_line}")
                return None
            
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
            
            return {
                'name': sensor_name,
                'pins': pins,
                'payload': payload,
                'is_new': is_new
            }
                
        except Exception as e:
            logger.error(f"Error parsing header '{header_line}': {e}")
            return None
    
    def _parse_data(self, data_line):
        """Parse regular data line format."""
        try:
            if ':' not in data_line:
                return None
            
            sensor_name, values_str = data_line.split(':', 1)
            sensor_name = sensor_name.strip()
            
            # Update last seen time
            if sensor_name in self.discovered_sensors:
                self.discovered_sensors[sensor_name]['last_seen'] = time.time()
            
            # Parse values
            data_values = [v.strip() for v in values_str.split(',')]
            
            return {
                'name': sensor_name,
                'values': data_values
            }
                
        except Exception as e:
            logger.debug(f"Error parsing data line '{data_line}': {e}")
            return None
    
    def _log_status(self):
        """Log periodic status information."""
        with self.buffer_lock:
            buffer_usage = len(self.data_buffer)
            oldest_time = self.data_buffer[0][0] if self.data_buffer else None
            newest_time = self.data_buffer[-1][0] if self.data_buffer else None
        
        connection_status = "Connected" if (self.serial_conn and self.serial_conn.is_open) else "Disconnected"
        client_count = len(self.connected_clients)
        
        logger.info(f"Serial Status - Connection: {connection_status}, "
                   f"Lines read: {self.lines_read_count}, "
                   f"Bytes read: {self.bytes_read_count}, "
                   f"Buffer entries: {buffer_usage}, "
                   f"Discovered sensors: {len(self.discovered_sensors)}, "
                   f"Connected clients: {client_count}")
        
        if oldest_time and newest_time:
            buffer_span = newest_time - oldest_time
            logger.info(f"Buffer span: {buffer_span:.2f}s (retention: {self.DATA_RETENTION_SECONDS}s)")
        
        if self.discovered_sensors:
            sensor_names = list(self.discovered_sensors.keys())
            logger.info(f"Active sensors: {sensor_names}")
    
    def _tcp_server_loop(self):
        """TCP server loop to accept client connections."""
        logger.info("Starting TCP server...")
        
        try:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_server.bind(('localhost', self.tcp_port))
            self.tcp_server.listen(5)
            logger.info(f"TCP server listening on localhost:{self.tcp_port}")
            
            while self.tcp_running:
                try:
                    client_socket, client_address = self.tcp_server.accept()
                    logger.info(f"New client connected from {client_address}")
                    
                    # Add to client list
                    self.connected_clients.append(client_socket)
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        name=f"Client-{client_address[0]}:{client_address[1]}",
                        daemon=True
                    )
                    client_thread.start()
                    
                    # Send initial status to new client
                    with self.buffer_lock:
                        buffer_size = len(self.data_buffer)
                    
                    self._send_to_client(client_socket, {
                        'type': 'server_status',
                        'serial_connected': self.serial_conn and self.serial_conn.is_open,
                        'discovered_sensors': list(self.discovered_sensors.keys()),
                        'buffer_size': buffer_size,
                        'retention_seconds': self.DATA_RETENTION_SECONDS
                    })
                    
                except socket.error as e:
                    if self.tcp_running:
                        logger.error(f"TCP server error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
        finally:
            if self.tcp_server:
                self.tcp_server.close()
        
        logger.info("TCP server stopped")
    
    def _handle_client(self, client_socket, client_address):
        """Handle individual client connection and process requests."""
        logger.info(f"Client handler started for {client_address}")
        
        try:
            # Send periodic status updates instead of waiting for requests
            last_status_time = 0
            message_buffer = ""
            
            # Set non-blocking mode
            client_socket.settimeout(1.0)
            
            while self.tcp_running:
                try:
                    # Try to receive data from client (requests)
                    try:
                        data = client_socket.recv(1024).decode('utf-8')
                        if not data:
                            break  # Client disconnected
                        
                        message_buffer += data
                        
                        # Process complete messages (separated by newlines)
                        while '\n' in message_buffer:
                            message_line, message_buffer = message_buffer.split('\n', 1)
                            message_line = message_line.strip()
                            
                            if message_line:
                                logger.info(f"Received request from client {client_address}: {message_line}")
                                self._process_client_request(client_socket, client_address, message_line)
                    
                    except socket.timeout:
                        # No data received, continue to periodic updates
                        pass
                    
                    # Send periodic updates to keep connection alive and provide data
                    current_time = time.time()
                    if current_time - last_status_time >= 0.5:  # Every 500ms
                        # Get recent data
                        recent_data = self._get_data_range(current_time - 1.0, current_time, ['discovery', 'sensor_data'])
                        
                        if recent_data:  # Only send if there's new data
                            status_update = {
                                'type': 'periodic_update',
                                'data': recent_data,
                                'timestamp': current_time
                            }
                            self._send_to_client(client_socket, status_update)
                            logger.debug(f"📤 Sent periodic update to {client_address} with {len(recent_data)} entries")
                        
                        last_status_time = current_time
                
                except socket.error as e:
                    logger.warning(f"Socket error with client {client_address}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {client_address}: {e}")
                    break
                
        except Exception as e:
            logger.debug(f"Client {client_address} handler error: {e}")
        finally:
            # Remove client from list
            if client_socket in self.connected_clients:
                self.connected_clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"Client {client_address} disconnected")
    
    def _broadcast_to_clients(self, message):
        """Broadcast a message to all connected clients."""
        if not self.connected_clients:
            return
        
        try:
            message_json = json.dumps(message) + '\n'
            message_bytes = message_json.encode('utf-8')
            
            # Send to all clients (remove disconnected ones)
            disconnected_clients = []
            for client in self.connected_clients:
                try:
                    client.send(message_bytes)
                except:
                    disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                if client in self.connected_clients:
                    self.connected_clients.remove(client)
                try:
                    client.close()
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Error broadcasting to clients: {e}")
    
    def _send_to_client(self, client_socket, message):
        """Send a message to a specific client."""
        try:
            message_json = json.dumps(message) + '\n'
            message_bytes = message_json.encode('utf-8')
            client_socket.send(message_bytes)
        except Exception as e:
            logger.debug(f"Error sending to client: {e}")
    
    def _process_client_request(self, client_socket, client_address, request_line):
        """Process a request from a client and send response."""
        try:
            request = json.loads(request_line)
            request_type = request.get('type')
            request_id = request.get('request_id', 'unknown')
            
            logger.info(f"Processing {request_type} request {request_id} from {client_address}")
            
            if request_type == 'get_data':
                # Get data from specific time range
                from_time = request.get('from_time', time.time() - 1.0)  # Default: last 1 second
                to_time = request.get('to_time', time.time())
                data_types = request.get('data_types', ['discovery', 'sensor_data'])  # What types to include
                
                response_data = self._get_data_range(from_time, to_time, data_types)
                logger.info(f"Found {len(response_data)} entries for request {request_id} (time range: {from_time:.2f} to {to_time:.2f})")
                
                response = {
                    'type': 'data_response',
                    'request_id': request_id,
                    'data': response_data,
                    'from_time': from_time,
                    'to_time': to_time
                }
                self._send_to_client(client_socket, response)
                logger.info(f"Sent data_response for request {request_id} with {len(response_data)} entries")
                
            elif request_type == 'get_status':
                # Get server status
                with self.buffer_lock:
                    buffer_size = len(self.data_buffer)
                    oldest_entry_time = self.data_buffer[0][0] if self.data_buffer else None
                    newest_entry_time = self.data_buffer[-1][0] if self.data_buffer else None
                
                response = {
                    'type': 'status_response',
                    'request_id': request_id,
                    'serial_connected': self.serial_conn and self.serial_conn.is_open,
                    'discovered_sensors': list(self.discovered_sensors.keys()),
                    'buffer_size': buffer_size,
                    'oldest_entry_time': oldest_entry_time,
                    'newest_entry_time': newest_entry_time,
                    'retention_seconds': self.DATA_RETENTION_SECONDS
                }
                self._send_to_client(client_socket, response)
                logger.info(f"✅ Sent status_response for request {request_id}")
                
            else:
                # Unknown request type
                logger.warning(f"❌ Unknown request type: {request_type}")
                response = {
                    'type': 'error_response',
                    'request_id': request_id,
                    'error': f'Unknown request type: {request_type}'
                }
                self._send_to_client(client_socket, response)
                logger.info(f"✅ Sent error_response for request {request_id}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from client {client_address}: {request_line}")
            response = {
                'type': 'error_response',
                'error': f'Invalid JSON: {e}'
            }
            self._send_to_client(client_socket, response)
        except Exception as e:
            logger.error(f"Error processing request from {client_address}: {e}")
            response = {
                'type': 'error_response',
                'error': f'Server error: {e}'
            }
            self._send_to_client(client_socket, response)
    
    def _get_data_range(self, from_time: float, to_time: float, data_types: List[str]) -> List[Dict]:
        """Get data from buffer within the specified time range."""
        result = []
        
        with self.buffer_lock:
            for timestamp, data_type, content in self.data_buffer:
                # Check if within time range and type filter
                if from_time <= timestamp <= to_time and data_type in data_types:
                    entry = {
                        'timestamp': timestamp,
                        'type': data_type,
                        **content  # Spread the content dict
                    }
                    result.append(entry)
        
        # Sort by timestamp (should already be sorted, but just to be sure)
        result.sort(key=lambda x: x['timestamp'])
        return result


def detect_arduino_port():
    """Detect Arduino COM port automatically."""
    try:
        import serial.tools.list_ports
    except ImportError:
        print("ERROR: pyserial not installed. Run: pip install pyserial")
        return None
    
    for port in serial.tools.list_ports.comports():
        # Look for Arduino identifiers
        if any(identifier in port.description.lower() for identifier in ['arduino', 'ch340', 'cp210', 'ftdi']):
            logger.info(f"Found Arduino on {port.device}: {port.description}")
            return port.device
    
    # Also check specific COM ports commonly used by Arduino
    for port_num in range(1, 20):
        port_name = f"COM{port_num}"
        try:
            test_serial = serial.Serial(port_name, timeout=1)
            test_serial.close()
            logger.info(f"Found available serial port: {port_name}")
            return port_name
        except:
            continue
    
    return None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    if 'server' in globals():
        server.stop()
    sys.exit(0)


def main():
    """Main entry point for the serial server."""
    parser = argparse.ArgumentParser(description="Serial Communication Server")
    parser.add_argument("--port", help="Serial port (e.g., COM6)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--tcp-port", type=int, default=9999, help="TCP server port")
    parser.add_argument("--auto-detect", action="store_true", help="Auto-detect Arduino port")
    
    args = parser.parse_args()
    
    # Determine serial port
    serial_port = args.port
    if args.auto_detect or not serial_port:
        detected_port = detect_arduino_port()
        if detected_port:
            serial_port = detected_port
            logger.info(f"Auto-detected Arduino on {serial_port}")
        else:
            logger.error("No Arduino found. Please specify --port manually.")
            sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start server
    global server
    server = SerialCommunicationServer(serial_port, args.baudrate, args.tcp_port)
    
    try:
        server.start()
        
        # Keep main thread alive
        logger.info("Serial Communication Server is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down on user request...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()