"""Main page for sensor dashboard."""
from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, Any

from ui.components.sensor import SensorGrid, SensorSelector, SensorSummary
from ui.components.common import IntervalComponent
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorDashboardPage:
    """Main sensor dashboard page."""
    
    def __init__(self, sensor_names: list):
        self.sensor_names = sensor_names
        self.sensor_grid = SensorGrid()
        self.sensor_selector = SensorSelector(sensor_names)
        self.sensor_summary = SensorSummary()
        
        # Add all sensors to grid initially
        for sensor_name in sensor_names:
            self.sensor_grid.add_sensor(sensor_name)
    
    def create_layout(self) -> html.Div:
        """Create the sensor dashboard layout."""
        return dbc.Container([
            # Sensor selector and summary row
            dbc.Row([
                dbc.Col([
                    self.sensor_selector.create()
                ], width=12, md=8),
                dbc.Col([
                    self.sensor_summary.create(
                        total_sensors=len(self.sensor_names),
                        active_sensors=0  # Will be updated by callbacks
                    )
                ], width=12, md=4)
            ], className="mb-4"),
            
            # Sensor grid
            self.sensor_grid.create(),
            
            # Update interval
            IntervalComponent.create("sensor-update-interval", 2000)
            
        ], fluid=True, id="sensor-dashboard-page")