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


class MicrocontrollerIOMap:
    """Microcontroller I/O pin mapping visualization component."""
    
    def __init__(self, sensor_names: List[str], has_connected_hardware: bool = False):
        self.sensor_names = sensor_names
        self.has_connected_hardware = has_connected_hardware
        # Define pin mappings (this would typically come from configuration)
        self.pin_mappings = self._generate_pin_mappings(sensor_names) if has_connected_hardware else {}
    
    def _generate_pin_mappings(self, sensor_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate pin mappings for sensors."""
        # Example pin mapping - in a real application, this would come from config
        pin_types = ['Analog', 'Digital', 'I2C', 'SPI', 'UART']
        colors = ['primary', 'success', 'info', 'warning', 'secondary']
        
        mappings = {}
        for idx, sensor in enumerate(sensor_names):
            pin_type = pin_types[idx % len(pin_types)]
            mappings[sensor] = {
                'pin': f"A{idx}" if pin_type == 'Analog' else f"D{idx}",
                'type': pin_type,
                'color': colors[idx % len(colors)]
            }
        return mappings
    
    def create(self) -> dbc.Card:
        """Create microcontroller I/O visualization card."""
        # Check if we have pin mappings (hardware is connected)
        if not self.pin_mappings or not self.has_connected_hardware:
            # Show "no sensors connected" state
            card_content = dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-plug-circle-xmark fa-3x text-muted mb-3"),
                    html.H6("No Hardware Detected", className="text-muted mb-2"),
                    html.P(
                        "Microcontroller I/O mapping will appear here when hardware is connected.",
                        className="text-muted small mb-0",
                        style={'fontSize': '0.8rem'}
                    )
                ], className="text-center py-4", id="io-mapping-grid")
            ], className="p-3", style={'minHeight': '180px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
        else:
            # Create compact pin list with clean professional design
            pin_elements = []
            for sensor, info in self.pin_mappings.items():
                pin_row = html.Div([
                    html.Div([
                        dbc.Badge(
                            info['pin'],
                            color=info['color'],
                            className="fw-bold",
                            style={'fontSize': '0.7rem', 'padding': '0.25rem 0.5rem', 'minWidth': '32px', 'textAlign': 'center'}
                        )
                    ], style={'width': '45px', 'flexShrink': '0'}),
                    html.Div([
                        html.Span(sensor, className="fw-semibold", style={'fontSize': '0.875rem'})
                    ], className="flex-grow-1 px-2"),
                    html.Div([
                        html.Span(
                            info['type'],
                            className="text-muted small",
                            style={'fontSize': '0.75rem'}
                        )
                    ], style={'width': '60px', 'textAlign': 'right', 'flexShrink': '0'})
                ], className="d-flex align-items-center py-1 px-2 mb-1 io-pin-row",
                   style={
                       'borderLeft': f'3px solid var(--bs-{info["color"]})',
                       'backgroundColor': '#fafafa',
                       'borderRadius': '3px',
                       'transition': 'all 0.2s ease'
                   })
                
                pin_elements.append(pin_row)
            
            card_content = dbc.CardBody([
                html.Div(
                    pin_elements,
                    id="io-mapping-grid",
                    className="compact-io-list"
                )
            ], className="p-2", style={'maxHeight': '220px', 'overflowY': 'auto'})
        
        return dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H5("I/O Mapping", className="mb-0 d-inline", style={'fontSize': '1rem'})
                ])
            ], className="py-2"),
            card_content
        ], className="mb-3 shadow-sm", id="io-map-card")


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