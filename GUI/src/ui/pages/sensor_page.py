"""Main page for sensor dashboard."""
from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, Any

from ui.components.sensor import SensorGrid, SensorSelector, SensorSummary, TCPConsoleOutput
from ui.components.common import IntervalComponent
from core.dependencies import container
from services.tcp_communication_service import CommunicationService
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorDashboardPage:
    """Main sensor dashboard page."""
    
    def __init__(self, sensor_names: list):
        self.sensor_names = sensor_names
        self.sensor_grid = SensorGrid()
        self.sensor_selector = SensorSelector(sensor_names)
        self.sensor_summary = SensorSummary()
        
        # Check if hardware is connected
        try:
            comm_service = container.get(CommunicationService)
            has_connected_hardware = comm_service.is_connected()
        except Exception as e:
            logger.warning(f"Could not determine connection status: {e}")
            has_connected_hardware = False
        
        self.tcp_console = TCPConsoleOutput(has_connected_hardware=has_connected_hardware)
        
        # Add all sensors to grid initially
        for sensor_name in sensor_names:
            self.sensor_grid.add_sensor(sensor_name)
    
    def create_layout(self) -> html.Div:
        """Create the sensor dashboard layout."""
        return dbc.Container([
            # Top row: Left column (filter + TCP console) and Right column (summary)
            dbc.Row([
                # Left column: Sensor filter and TCP console stacked
                dbc.Col([
                    self.sensor_selector.create(),
                    self.tcp_console.create()
                ], width=12, lg=8, className="mb-3 mb-lg-0"),
                
                # Right column: Sensor summary (matches combined height of left)
                dbc.Col([
                    self.sensor_summary.create(
                        selected_sensors=len(self.sensor_names),
                        active_sensors=0  # Will be updated by callbacks based on watchdog timer
                    )
                ], width=12, lg=4)
            ], className="mb-4"),
            
            # Sensor grid with header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4("Sensor Data", className="mb-3 d-inline-block"),
                        html.Hr(className="mt-2 mb-3")
                    ]),
                    self.sensor_grid.create()
                ], width=12)
            ]),
            
            # Update interval
            IntervalComponent.create("sensor-update-interval", 2000)
            
        ], fluid=True, id="sensor-dashboard-page", className="py-3")
