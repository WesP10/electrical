"""Sensor-related callbacks."""
from dash.dependencies import Input, Output, State
from dash import html
import pandas as pd
from typing import List, Dict, Any

from core.dependencies import container
from services.sensor_service import SensorService
from ui.components.sensor import SensorCard
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorCallbacks:
    """Sensor callback manager."""
    
    def __init__(self):
        pass
    
    def register(self, app) -> None:
        """Register sensor-related callbacks."""
        self._register_sensor_update_callback(app)
        self._register_sensor_selector_callback(app)
    
    def _register_sensor_update_callback(self, app) -> None:
        """Register periodic sensor data update callback."""
        @app.callback(
            [Output('sensor-grid', 'children'),
             Output('sensor-summary-card', 'children')],
            [Input('sensor-update-interval', 'n_intervals'),
             Input('sensor-dropdown', 'value')]
        )
        def update_sensor_data(n_intervals, selected_sensors):
            """Update sensor data periodically."""
            try:
                # Get sensor service
                sensor_service = container.get(SensorService)
                
                if not selected_sensors:
                    return [], self._create_summary_content(0, 0)
                
                # Get sensor data
                sensor_data = sensor_service.get_all_sensor_data()
                
                # Create sensor cards for selected sensors
                sensor_cards = []
                active_count = 0
                
                for sensor_name in selected_sensors:
                    data = sensor_data.get(sensor_name)
                    if data is not None and not data.empty:
                        active_count += 1
                    
                    # Create sensor card
                    sensor_card = SensorCard(sensor_name)
                    card = sensor_card.create(data)
                    
                    # Wrap in column
                    from dash import html
                    import dash_bootstrap_components as dbc
                    sensor_cards.append(
                        dbc.Col(card, width=12, lg=6, xl=4)
                    )
                
                # Create summary content
                summary_content = self._create_summary_content(
                    len(selected_sensors), 
                    active_count
                )
                
                return sensor_cards, summary_content
                
            except Exception as e:
                logger.error(f"Error updating sensor data: {e}")
                return [], html.Div(f"Error: {e}")
    
    def _register_sensor_selector_callback(self, app) -> None:
        """Register sensor selector callback."""
        # This callback is handled by the update callback above
        # No additional callback needed
        pass
    
    def _create_summary_content(self, total: int, active: int) -> html.Div:
        """Create sensor summary content."""
        from ui.components.common import StatusIndicator
        
        return html.Div([
            html.P(f"Total Sensors: {total}"),
            html.P(f"Active Sensors: {active}"),
            html.P(f"Inactive Sensors: {total - active}"),
            StatusIndicator.create(
                "connected" if active > 0 else "disconnected",
                "sensors-status"
            )
        ])