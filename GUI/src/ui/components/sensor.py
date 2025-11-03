"""Sensor display components."""
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import List, Dict, Any, Optional

from ui.components.common import InfoCard, StatusIndicator, LoadingSpinner
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorCard:
    """Individual sensor card component."""
    
    def __init__(self, sensor_name: str):
        self.sensor_name = sensor_name
    
    def create(self, data: Optional[pd.DataFrame] = None, is_available: bool = True) -> dbc.Card:
        """Create a sensor card with graph and status."""
        # Create graph
        graph = self._create_graph(data, is_available)
        
        # Create status indicator
        status = "active" if is_available and data is not None and not data.empty else "inactive"
        
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
    
    def _create_graph(self, data: Optional[pd.DataFrame] = None, is_available: bool = True) -> dcc.Graph:
        """Create an empty graph that will be updated by callbacks."""
        # Create an empty figure - the callback will populate it
        fig = go.Figure()
        fig.add_annotation(
            text="Loading...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
            align="center"
        )
        
        fig.update_layout(
            title=f"{self.sensor_name}",
            xaxis_title="Time",
            yaxis_title="Value",
            height=300,
            margin=dict(l=50, r=30, t=50, b=50),
            xaxis=dict(
                showgrid=True, 
                zeroline=True,
                range=[0, 10],  # Show default range
                showticklabels=True
            ),
            yaxis=dict(
                showgrid=True, 
                zeroline=True,
                range=[0, 100],  # Show default range
                showticklabels=True
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.8)',
            paper_bgcolor='white'
        )
        
        return dcc.Graph(
            id=f"{self.sensor_name}-graph",
            figure=fig,
            style={'height': '300px', 'width': '100%'}
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
    
    def create(self) -> dbc.Card:
        """Create sensor selector card with modern styling."""
        return dbc.Card([
            dbc.CardHeader(
                html.H5("Sensor Filter", className="mb-0")
            ),
            dbc.CardBody([
                html.Label('Select Sensors to Display:', className="form-label text-muted mb-2 small"),
                dcc.Dropdown(
                    id='sensor-dropdown',
                    options=[{'label': name, 'value': name} for name in self.sensor_names],
                    multi=True,
                    value=self.sensor_names,  # Default to all sensors
                    placeholder="Choose sensors to display...",
                    className="mb-2"
                ),
                html.Div([
                    html.I(className="fas fa-info-circle me-1 text-muted"),
                    html.Small(
                        f"{len(self.sensor_names)} sensors available",
                        className="text-muted"
                    )
                ], className="d-flex align-items-center")
            ], className="p-3")
        ], className="mb-3 shadow-sm")


class TCPConsoleOutput:
    """TCP Communication console output component for debugging."""
    
    def __init__(self, has_connected_hardware: bool = False):
        self.has_connected_hardware = has_connected_hardware
    
    def create(self) -> dbc.Card:
        """Create TCP communication console card."""
        # Console content with scrollable output and auto-scroll
        card_content = dbc.CardBody([
            html.Div([
                html.Div(
                    id="tcp-console-output",
                    children=[
                        html.Div(
                            "Waiting for TCP communication data..." if self.has_connected_hardware 
                            else "No connection to serial server. Start serial server to see data.",
                            className="text-muted small",
                            style={'fontFamily': 'monospace', 'fontSize': '0.75rem'}
                        )
                    ],
                    style={
                        'backgroundColor': '#1e1e1e',
                        'color': '#d4d4d4',
                        'fontFamily': 'Consolas, Monaco, "Courier New", monospace',
                        'fontSize': '0.75rem',
                        'padding': '10px',
                        'borderRadius': '4px',
                        'maxHeight': '300px',
                        'minHeight': '300px',
                        'overflowY': 'auto',
                        'overflowX': 'hidden',
                        'wordWrap': 'break-word',
                        'display': 'flex',
                        'flexDirection': 'column'  # Normal direction, newest at bottom
                    }
                )
            ])
        ], className="p-2")
        
        return dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-terminal me-2"),
                        html.H5("TCP Communication Console", className="mb-0 d-inline", style={'fontSize': '1rem'}),
                        html.Small(" (Real-time)", className="text-muted ms-2", style={'fontSize': '0.7rem'})
                    ]),
                    dbc.Checkbox(
                        id="tcp-console-autoscroll",
                        label="Auto-scroll",
                        value=True,
                        className="form-check-inline"
                    )
                ], className="d-flex align-items-center justify-content-between")
            ], className="py-2"),
            card_content
        ], className="mb-3 shadow-sm", id="tcp-console-card")


class SensorSummary:
    """Sensor summary component."""
    
    def create(self, selected_sensors: int = 0, active_sensors: int = 0) -> dbc.Card:
        """Create sensor summary card."""
        inactive_sensors = selected_sensors - active_sensors
        
        return dbc.Card([
            dbc.CardHeader(
                html.H5("Sensor Summary", className="mb-0")
            ),
            dbc.CardBody([
                # Selected sensors
                html.Div([
                    html.Span("Selected Sensors", className="text-muted small d-block mb-1"),
                    html.H4(str(selected_sensors), className="mb-0 fw-bold text-primary")
                ], className="mb-3"),
                
                # Active sensors
                html.Div([
                    html.Span("Active", className="text-muted small d-block mb-1"),
                    html.H5(str(active_sensors), className="mb-0 fw-bold text-success")
                ], className="mb-3"),
                
                # Inactive sensors
                html.Div([
                    html.Span("Inactive", className="text-muted small d-block mb-1"),
                    html.H5(str(inactive_sensors), className="mb-0 fw-bold text-secondary")
                ], className="mb-3"),
                
                html.Hr(className="my-3"),
                
                # Overall status
                html.Div([
                    html.Span("System Status", className="text-muted small d-block mb-2"),
                    StatusIndicator.create(
                        "connected" if active_sensors > 0 else "disconnected",
                        "sensors-status"
                    )
                ])
            ], className="p-3")
        ], id="sensor-summary-card", className="mb-3 shadow-sm")
