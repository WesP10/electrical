"""
Navigation Bar Callbacks

Handles callbacks for the navigation bar components including:
- Port selection dropdown
- Baud rate selection dropdown  
- Connection status updates
-         # Add interval component for periodic status updates
        @app.callback(
            Output('navbar-interval-store', 'children'),
            [Input('url', 'pathname')],
            prevent_initial_call=False
        )
        def add_status_interval(pathname):
            \"\"\"Add interval component for periodic status updates.\"\"\"
            return dcc.Interval(
                id='connection-status-interval',
                interval=5000,  # Update every 5 seconds
                n_intervals=0
            )
        
        # Add callback to trigger sensor refresh when connection changes
        @app.callback(
            Output('sensor-refresh-trigger', 'data'),
            [Input('port-selection-dropdown', 'value'),
             Input('baud-rate-dropdown', 'value')],
            prevent_initial_call=True
        )
        def trigger_sensor_refresh(selected_port, selected_baud):
            \"\"\"Trigger sensor refresh when microcontroller connection changes.\"\"\"
            if selected_port and selected_baud:
                # Return timestamp to trigger refresh
                import time
                return {'timestamp': time.time(), 'port': selected_port, 'baud': selected_baud}
            return {'timestamp': 0}functionality
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

from dash import callback, Input, Output, State, no_update, ctx, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# Use PYTHONPATH for imports

from config.log_config import get_logger
from utils.port_detection import (
    get_port_dropdown_options, 
    get_baud_rate_dropdown_options,
    auto_detect_microcontroller,
    PortDetector
)
from core.dependencies import container
from services.tcp_communication_service import CommunicationService

logger = get_logger(__name__)


class NavigationBarCallbacks:
    """Handles navigation bar related callbacks."""
    
    def __init__(self):
        self.communication_service = None
        self._last_port_refresh = 0
        self._port_refresh_cooldown = 2.0  # Seconds
    
    def register_callbacks(self, app):
        """Register all navigation bar callbacks with the Dash app."""
        logger.info("REGISTERING NAVIGATION BAR CALLBACKS...")
        
        @app.callback(
            [Output('port-selection-dropdown', 'options'),
             Output('baud-rate-dropdown', 'options')],
            [Input('refresh-ports-button', 'n_clicks')],
            prevent_initial_call=False
        )
        def update_dropdown_options(refresh_clicks):
            """Update dropdown options when page loads or refresh is clicked."""
            logger.info(f"DROPDOWN CALLBACK TRIGGERED - refresh_clicks: {refresh_clicks}")
            try:
                # Implement cooldown to prevent excessive refreshing
                current_time = time.time()
                if (refresh_clicks and refresh_clicks > 0 and 
                    current_time - self._last_port_refresh < self._port_refresh_cooldown):
                    logger.debug("Port refresh on cooldown, skipping")
                    raise PreventUpdate
                
                if refresh_clicks and refresh_clicks > 0:
                    self._last_port_refresh = current_time
                    logger.info("Refreshing port and baud rate options")
                
                # Get current port and baud rate options
                logger.info("Getting port dropdown options...")
                port_options = get_port_dropdown_options()
                logger.info("Getting baud rate dropdown options...")
                baud_rate_options = get_baud_rate_dropdown_options()
                
                logger.info(f"DROPDOWN UPDATE SUCCESS: {len(port_options)} port options and {len(baud_rate_options)} baud rate options")
                logger.info(f"Port options: {port_options}")
                
                return port_options, baud_rate_options
                
            except Exception as e:
                logger.error(f"Error updating dropdown options: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Return empty options on error
                return [], []
        
        @app.callback(
            [Output('port-selection-dropdown', 'value'),
             Output('baud-rate-dropdown', 'value'),
             Output('connection-status-indicator', 'children')],
            [Input('port-selection-dropdown', 'options')],
            [State('port-selection-dropdown', 'value'),
             State('baud-rate-dropdown', 'value')],
            prevent_initial_call=False
        )
        def initialize_default_values(port_options, current_port, current_baud):
            """Initialize default values for dropdowns based on auto-detection."""
            if not port_options:
                return no_update, no_update, no_update
            
            try:
                # If no current selection, try to auto-detect
                if not current_port:
                    detected = auto_detect_microcontroller()
                    if detected:
                        detected_port, detected_baud = detected
                        logger.info(f"Auto-detected microcontroller: {detected_port} at {detected_baud} baud")
                        
                        # Update status indicator
                        status_children = [
                            html.I(className="fas fa-circle text-success me-1"),
                            html.Span("Auto-detected")
                        ]
                        
                        return detected_port, detected_baud, status_children
                    else:
                        logger.info("No microcontroller detected")
                        status_children = [
                            html.I(className="fas fa-circle text-secondary me-1"), 
                            html.Span("No Hardware")
                        ]
                        return None, current_baud or 115200, status_children
                
                return no_update, no_update, no_update
                
            except Exception as e:
                logger.error(f"Error initializing default values: {e}")
                return no_update, no_update, no_update
        
        @app.callback(
            [Output('connection-status-icon', 'className'),
             Output('connection-status-text', 'children')],
            [Input('port-selection-dropdown', 'value'),
             Input('baud-rate-dropdown', 'value'),
             Input('connection-status-interval', 'n_intervals')],
            prevent_initial_call=True
        )
        def handle_connection_change(selected_port, selected_baud, n_intervals):
            """Handle changes to port or baud rate selection and periodic status updates."""
            triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
            
            # Handle dropdown changes
            if 'port-selection-dropdown' in str(triggered_id) or 'baud-rate-dropdown' in str(triggered_id):
                if not selected_port or not selected_baud:
                    raise PreventUpdate
                
                try:
                    logger.info(f"Connection change requested: {selected_port} at {selected_baud} baud")
                    
                    # Update connection to hardware
                    success = self._switch_to_hardware_mode(selected_port, selected_baud)
                    if success:
                        return (
                            "fas fa-circle text-success",
                            f"Connected to {selected_port}"
                        )
                    else:
                        return (
                            "fas fa-circle text-danger",
                            f"Failed to connect to {selected_port}"
                        )
                            
                except Exception as e:
                    logger.error(f"Error handling connection change: {e}")
                    return (
                        "fas fa-circle text-danger",
                        "Error"
                    )
            
            # Handle periodic status updates
            elif 'connection-status-interval' in str(triggered_id):
                status_icon, status_text, _, _ = self._get_current_connection_status(selected_port)
                return status_icon, status_text
            
            else:
                raise PreventUpdate
        
        # Add interval component for periodic status updates
        @app.callback(
            Output('navbar-interval-store', 'children'),
            [Input('url', 'pathname')],
            prevent_initial_call=False
        )
        def add_status_interval(pathname):
            """Add interval component for periodic status updates."""
            return dcc.Interval(
                id='connection-status-interval',
                interval=5000,  # Update every 5 seconds
                n_intervals=0
            )
        
    def _get_communication_service(self) -> Optional[CommunicationService]:
        """Get the communication service instance."""
        if not self.communication_service:
            try:
                if container.has(CommunicationService):
                    self.communication_service = container.get(CommunicationService)
                else:
                    logger.warning("CommunicationService not found in container")
                    return None
            except Exception as e:
                logger.error(f"Error getting communication service: {e}")
                return None
        return self.communication_service
    

    def _switch_to_hardware_mode(self, port: str, baud_rate: int) -> bool:
        """Switch communication service to hardware mode with specified port and baud rate."""
        try:
            logger.info(f"Switching to hardware mode: {port} at {baud_rate} baud")
            
            # Test if port is available first
            if not PortDetector.test_port_connection(port, baud_rate):
                logger.warning(f"Cannot connect to {port} at {baud_rate} baud")
                return False
            
            # Start serial server if needed
            if not self._ensure_serial_server_running(port, baud_rate):
                logger.error("Failed to start serial server")
                return False
            
            # Clear existing sensors when switching modes
            self._clear_sensors_for_mode_switch()
            
            # Get communication service and switch to hardware mode
            comm_service = self._get_communication_service()
            if comm_service:
                success = comm_service.switch_to_hardware_mode(port, baud_rate)
                if success:
                    logger.info(f"Successfully switched to hardware mode: {port} at {baud_rate} baud")
                    return True
                else:
                    logger.error("Communication service failed to switch to hardware mode")
                    return False
            else:
                # Fallback: just set environment variables
                os.environ["SERIAL_SERVER_MODE"] = "true"
                os.environ["SERIAL_PORT"] = port
                os.environ["SERIAL_BAUD_RATE"] = str(baud_rate)
                logger.warning("Communication service not available, using environment variables")
                return True
            
        except Exception as e:
            logger.error(f"Error switching to hardware mode: {e}")
            return False
    
    def _get_current_connection_status(self, selected_port: str) -> Tuple[str, str, str, str]:
        """Get current connection status for periodic updates."""
        try:
            comm_service = self._get_communication_service()
            if not comm_service:
                return (
                    "fas fa-circle text-secondary",
                    "Service Unavailable",
                    "secondary",
                    "Unavailable"
                )
            
            # Get current mode information
            mode_info = comm_service.get_current_mode()
            
            if mode_info.get('connected', False):
                port = mode_info.get('port', 'Unknown')
                return (
                    "fas fa-circle text-success",
                    f"Connected to {port}",
                    "success",
                    "Connected"
                )
            else:
                error = mode_info.get('error', 'Disconnected')
                return (
                    "fas fa-circle text-danger",
                    f"Disconnected ({error})",
                    "danger",
                    "Disconnected"
                )
                
        except Exception as e:
            logger.debug(f"Error getting connection status: {e}")
            return (
                "fas fa-circle text-secondary",
                "Status Unknown",
                "secondary",
                "Unknown"
            )
    
    def _ensure_serial_server_running(self, port: str, baud_rate: int) -> bool:
        """Ensure the serial server is running for the specified port and baud rate."""
        try:
            import socket
            import subprocess
            import sys
            from pathlib import Path
            
            # Check if server is already running on port 9999
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = test_socket.connect_ex(('localhost', 9999))
                test_socket.close()
                if result == 0:
                    logger.info("Serial server already running on port 9999")
                    return True
            except:
                pass
            
            logger.info(f"Starting serial server for {port} at {baud_rate} baud")
            
            # Path to the serial server script
            from services.serial_server import __file__ as server_file
            server_script = Path(server_file)
            
            if not server_script.exists():
                logger.error(f"Serial server script not found: {server_script}")
                return False
            
            # Start the server process
            cmd = [
                sys.executable,
                str(server_script),
                "--port", port,
                "--baudrate", str(baud_rate),
                "--tcp-port", "9999"
            ]
            
            logger.info(f"Starting server with command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                cwd=server_script.parent.parent.parent,  # Navigate to project root
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )
            
            # Give the server time to start
            time.sleep(3)
            
            # Check if server is now running
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = test_socket.connect_ex(('localhost', 9999))
                test_socket.close()
                if result == 0:
                    logger.info(f"Serial server successfully started (PID: {process.pid})")
                    return True
                else:
                    logger.error("Serial server failed to start - port 9999 not available")
                    return False
            except Exception as e:
                logger.error(f"Error checking server status: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting serial server: {e}")
            return False
    
    def _clear_sensors_for_mode_switch(self) -> None:
        """Clear all sensors when switching communication modes."""
        try:
            logger.info("Clearing sensors for mode switch...")
            
            # Clear sensors from communication service
            comm_service = self._get_communication_service()
            if comm_service and hasattr(comm_service, 'clear_discovered_sensors'):
                comm_service.clear_discovered_sensors()
            
            # Clear sensors from sensor service
            from services.sensor_service import SensorService
            if container.has(SensorService):
                sensor_service = container.get(SensorService)
                sensor_service.clear_all_sensors()
            
            logger.info("Sensor clearing completed")
            
        except Exception as e:
            logger.error(f"Error clearing sensors for mode switch: {e}")
