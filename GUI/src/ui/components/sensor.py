"""Sensor display components."""
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import List, Dict, Any, Optional

from ui.components.common import InfoCard, StatusIndicator, LoadingSpinner
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorCard:
    """Individual sensor card component."""
    
    def __init__(self, sensor_name: str):
        self.sensor_name = sensor_name
    
    def create(self, data: Optional[pd.DataFrame] = None) -> dbc.Card:
        """Create a sensor card with graph and status."""
        # Create graph
        graph = self._create_graph(data)
        
        # Create status indicator
        status = "active" if data is not None and not data.empty else "inactive"
        
        return dbc.Card([
            dbc.CardHeader([
                html.H6(self.sensor_name, className="mb-0 d-inline"),
                StatusIndicator.create(status, f"{self.sensor_name}-status")
            ]),
            dbc.CardBody([
                LoadingSpinner.create(
                    f"{self.sensor_name}-graph-container",
                    graph
                ),
                html.Div(id=f"{self.sensor_name}-info", className="mt-2")
            ])
        ], className="mb-3")
    
    def _create_graph(self, data: Optional[pd.DataFrame] = None) -> dcc.Graph:
        """Create a graph for sensor data."""
        if data is None or data.empty:
            # Empty graph
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.sensor_name} - No Data",
                xaxis_title="Time",
                yaxis_title="Value"
            )
        else:
            # Create traces for each data column (excluding Time)
            fig = go.Figure()
            for column in data.columns:
                if column != 'Time':
                    fig.add_trace(go.Scatter(
                        x=data['Time'],
                        y=data[column],
                        mode='lines',
                        name=column
                    ))
            
            fig.update_layout(
                title=f"{self.sensor_name} Data",
                xaxis_title="Time",
                yaxis_title="Value",
                height=300
            )
        
        return dcc.Graph(
            id=f"{self.sensor_name}-graph",
            figure=fig
        )


class SensorGrid:
    """Grid container for sensor cards."""
    
    def __init__(self):
        self.sensor_cards: List[SensorCard] = []
    
    def add_sensor(self, sensor_name: str) -> None:
        """Add a sensor to the grid."""
        self.sensor_cards.append(SensorCard(sensor_name))
    
    def create(self, sensor_data: Dict[str, pd.DataFrame] = None) -> dbc.Row:
        """Create the sensor grid."""
        if sensor_data is None:
            sensor_data = {}
        
        columns = []
        for sensor_card in self.sensor_cards:
            data = sensor_data.get(sensor_card.sensor_name)
            card = sensor_card.create(data)
            columns.append(
                dbc.Col(card, width=12, lg=6, xl=4)
            )
        
        return dbc.Row(columns, id="sensor-grid")


class SensorSelector:
    """Sensor selection dropdown component."""
    
    def __init__(self, sensor_names: List[str]):
        self.sensor_names = sensor_names
    
    def create(self) -> html.Div:
        """Create sensor selector dropdown."""
        return html.Div([
            html.Label('Select Sensors:', className="form-label"),
            dcc.Dropdown(
                id='sensor-dropdown',
                options=[{'label': name, 'value': name} for name in self.sensor_names],
                multi=True,
                value=self.sensor_names,  # Default to all sensors
                className="mb-3"
            )
        ])


class SensorSummary:
    """Sensor summary component."""
    
    def create(self, total_sensors: int = 0, active_sensors: int = 0) -> dbc.Card:
        """Create sensor summary card."""
        return InfoCard.create(
            title="Sensor Summary",
            content=[
                html.P(f"Total Sensors: {total_sensors}"),
                html.P(f"Active Sensors: {active_sensors}"),
                html.P(f"Inactive Sensors: {total_sensors - active_sensors}"),
                StatusIndicator.create(
                    "connected" if active_sensors > 0 else "disconnected",
                    "sensors-status"
                )
            ],
            card_id="sensor-summary-card"
        )