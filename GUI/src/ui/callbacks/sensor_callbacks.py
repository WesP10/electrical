"""Sensor-related callbacks."""
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd
from typing import List, Dict, Any
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import datetime
import numpy as np
import json

from core.dependencies import container
from services.sensor_service import SensorService
from ui.components.sensor import SensorCard
import sys
from pathlib import Path

# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)


class SensorCallbacks:
    """Sensor callback manager."""
    
    def __init__(self):
        pass
    
    def register(self, app) -> None:
        """Register sensor-related callbacks."""
        self._register_sensor_update_callback(app)
        self._register_tcp_console_callback(app)
    
    def _register_sensor_update_callback(self, app) -> None:
        """Register periodic sensor data update callback."""
        @app.callback(
            [Output('sensor-grid', 'children'),
             Output('sensor-summary-card', 'children')],
            [Input('sensor-update-interval', 'n_intervals'),
             Input('sensor-dropdown', 'value'),
             Input('sensor-refresh-trigger', 'data')]
        )
        def update_sensor_data(n_intervals, selected_sensors, refresh_trigger):
            """Update sensor data periodically and when microcontroller changes."""
            try:
                logger.info(f"Callback triggered: interval={n_intervals}, sensors={selected_sensors}, refresh={refresh_trigger}")
                
                # Get TCP communication service directly
                from services.tcp_communication_service import CommunicationService
                tcp_service = container.get(CommunicationService)
                
                if not selected_sensors:
                    logger.warning("No sensors selected")
                    return [], self._create_summary_content(0, 0)
                
                # Create sensor cards for selected sensors
                sensor_cards = []
                active_count = 0
                
                for sensor_name in selected_sensors:
                    # Find the sensor ID that corresponds to this sensor name
                    from sensors.sensor_registry import sensor_registry
                    sensor_id = None
                    for sid, info in sensor_registry.sensor_classes.items():
                        if info['name'] == sensor_name:
                            sensor_id = sid
                            break
                    
                    if not sensor_id:
                        logger.warning(f"Could not find sensor ID for sensor name: {sensor_name}")
                        is_available = False
                        data = None
                    else:
                        # Directly check TCP communication service for sensor data
                        logger.info(f"Querying TCP service for sensor: {sensor_name}")
                        is_available = tcp_service.has_recent_data_for_sensor(sensor_name)
                        logger.info(f"TCP service returned availability for {sensor_name}: {is_available}")
                        
                        if is_available:
                            data = tcp_service.get_sensor_data_dataframe(sensor_name)
                            logger.info(f"Got dataframe for {sensor_name}: {len(data) if data is not None else 0} rows")
                        else:
                            data = None
                            logger.info(f"No data available for {sensor_name}")
                    
                    # Count as active only if available (based on recent data)
                    if is_available:
                        active_count += 1
                        logger.info(f"Sensor {sensor_name}: Available (recent data)")
                    else:
                        logger.info(f"Sensor {sensor_name}: Unavailable (no recent data)")
                    
                    # Create sensor card with actual graph data
                    sensor_card = SensorCard(sensor_name)
                    card = self._create_sensor_card_with_graph(sensor_name, data, is_available, sensor_id)
                    
                    # Wrap in column (made wider: xl=6 instead of xl=4)
                    sensor_cards.append(
                        dbc.Col(card, width=12, lg=6, xl=6)
                    )
                
                logger.info(f"Created {len(sensor_cards)} sensor cards, {active_count} active (based on recent data)")
                
                # Create summary content with selected sensors count and recent data availability
                summary_content = self._create_summary_content(
                    len(selected_sensors), 
                    active_count
                )
                
                return sensor_cards, summary_content
                
            except Exception as e:
                logger.error(f"Error updating sensor data: {e}", exc_info=True)
                error_content = [
                    html.Div(f"Error loading sensor summary: {e}", className="p-3 text-danger")
                ]
                return [], error_content
    
    def _create_summary_content(self, selected: int, active: int) -> list:
        """Create sensor summary content with proper styling."""
        from ui.components.common import StatusIndicator
        
        inactive = selected - active
        
        return [
            dbc.CardHeader(
                html.H5("Sensor Summary", className="mb-0")
            ),
            dbc.CardBody([
                # Selected sensors
                html.Div([
                    html.Div([
                        html.Span("Selected Sensors", className="text-muted"),
                        html.H4(str(selected), className="mb-0 mt-1 fw-bold text-primary")
                    ], className="mb-3")
                ]),
                
                # Active sensors
                html.Div([
                    html.Div([
                        html.Span("Active", className="text-muted"),
                        html.Div([
                            html.H5(str(active), className="mb-0 mt-1 fw-bold text-success d-inline me-2"),
                            dbc.Badge("?", color="success", className="align-middle")
                        ])
                    ], className="mb-3")
                ]),
                
                # Inactive sensors
                html.Div([
                    html.Div([
                        html.Span("Inactive", className="text-muted"),
                        html.Div([
                            html.H5(str(inactive), className="mb-0 mt-1 fw-bold text-secondary d-inline me-2"),
                            dbc.Badge("?", color="secondary", className="align-middle")
                        ])
                    ], className="mb-2")
                ]),
                
                html.Hr(className="my-3"),
                
                # Overall status
                html.Div([
                    html.Span("Status: ", className="text-muted"),
                    StatusIndicator.create(
                        "connected" if active > 0 else "disconnected",
                        "sensors-status"
                    )
                ], className="d-flex align-items-center")
            ], className="p-3")
        ]
    
    def _create_sensor_card_with_graph(self, sensor_name: str, data: pd.DataFrame, is_available: bool, sensor_id: str) -> html.Div:
        """Create a sensor card with proper graphs using actual sensor data fields."""
        
        # Get sensor information from registry
        from sensors.sensor_registry import sensor_registry
        sensor_info = sensor_registry.get_sensor_info(sensor_id)
        
        if not sensor_info:
            # Fallback to single graph if sensor info not found
            return self._create_fallback_sensor_card(sensor_name, data, is_available)
        
        data_fields = sensor_info.get('data_fields', [])
        units = sensor_info.get('units', {})
        
        # Create multiple graphs for each data field
        graphs = []
        
        if is_available and data is not None and not data.empty:
            # Create a graph for each data field using REAL DATA
            for field in data_fields:
                fig = self._create_sensor_field_graph(sensor_name, field, units.get(field, ''), sensor_id, data)
                graphs.append(
                    html.Div([
                        dcc.Graph(
                            id=f"{sensor_name.replace(' ', '-').lower()}-{field}-graph",
                            figure=fig,
                            style={'height': '300px', 'width': '100%'}
                        )
                    ], className="mb-2")
                )
            status = "active"
        else:
            # Create empty state graphs for each data field
            for field in data_fields:
                fig = self._create_empty_field_graph(sensor_name, field, units.get(field, ''))
                graphs.append(
                    html.Div([
                        dcc.Graph(
                            id=f"{sensor_name.replace(' ', '-').lower()}-{field}-graph",
                            figure=fig,
                            style={'height': '300px', 'width': '100%'}
                        )
                    ], className="mb-2")
                )
            status = "inactive"
        
        # If no data fields, show single graph
        if not graphs:
            fig = self._create_empty_graph(sensor_name) if not is_available else self._create_sensor_graph(sensor_name, data, sensor_id)
            graphs = [
                html.Div([
                    dcc.Graph(
                        id=f"{sensor_name.replace(' ', '-').lower()}-graph",
                        figure=fig,
                        style={'height': '300px', 'width': '100%'}
                    )
                ], className="mb-2")
            ]
        
        # Create status indicator
        from ui.components.common import StatusIndicator
        status_indicator = StatusIndicator.create(status, f"{sensor_name}-status")
        
        return dbc.Card([
            dbc.CardHeader([
                html.H6(sensor_name, className="mb-0 d-inline"),
                html.Div(status_indicator, className="float-end")
            ]),
            dbc.CardBody([
                html.Div(graphs),  # Multiple graphs container
                html.Div(
                    self._create_sensor_info(sensor_name, data, is_available, len(data_fields)),
                    className="mt-2"
                )
            ])
        ], className="mb-3")
    
    def _create_sensor_graph(self, sensor_name: str, data: pd.DataFrame, sensor_id: str) -> go.Figure:
        """Create a proper graph for sensor data using actual values from TCP."""
        
        # Create the plot
        fig = go.Figure()
        
        # Check if we have actual data
        if data is not None and not data.empty and 'Time' in data.columns:
            # Use actual data from the DataFrame
            time_points = data['Time']
            
            # Determine which value column(s) to plot
            value_columns = [col for col in data.columns if col.startswith('value')]
            
            if value_columns:
                for col in value_columns:
                    values = data[col]
                    
                    # Determine color and y-axis label based on sensor type
                    y_title, color = self._get_sensor_display_info(sensor_name)
                    
                    # Add the trace with actual data
                    fig.add_trace(go.Scatter(
                        x=time_points,
                        y=values,
                        mode='lines+markers',
                        name=col if len(value_columns) > 1 else sensor_name,
                        line=dict(color=color, width=2),
                        marker=dict(size=4, color=color),
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                     'Time: %{x}<br>' +
                                     'Value: %{y:.2f}<br>' +
                                     '<extra></extra>'
                    ))
                
                logger.info(f"Plotted {len(values)} real data points for {sensor_name}")
            else:
                # No value columns found
                y_title = "Value"
                color = '#495057'
        else:
            # No data available - show empty state
            y_title = "Value"
            color = '#495057'
            time_points = []
            values = []
            
            fig.add_trace(go.Scatter(
                x=[],
                y=[],
                mode='lines',
                name=sensor_name
            ))
            
            fig.add_annotation(
                text="Waiting for data...",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="gray"),
                align="center"
            )
        
        # Update layout for professional look with uirevision to preserve zoom/pan
        fig.update_layout(
            title=dict(
                text=f"{sensor_name} - Live Data",
                font=dict(size=14, color='#495057'),
                x=0.02,
                xanchor='left'
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='rgba(128, 128, 128, 0.5)',
                tickformat='%H:%M:%S'
            ),
            yaxis=dict(
                title=y_title,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='rgba(128, 128, 128, 0.5)'
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.8)',
            paper_bgcolor='white',
            height=300,
            margin=dict(l=60, r=30, t=40, b=50),
            showlegend=False,
            hovermode='x unified',
            uirevision=f"{sensor_name}-main"  # Preserve zoom/pan state
        )
        
        return fig
    
    def _get_sensor_display_info(self, sensor_name: str):
        """Get appropriate y-axis label and color based on sensor type."""
        sensor_lower = sensor_name.lower()
        
        if 'temperature' in sensor_lower or 'thermistor' in sensor_lower:
            return "Temperature (°C)", '#d63384'  # Pink
        elif 'pressure' in sensor_lower:
            return "Pressure (hPa)", '#0d6efd'  # Blue
        elif 'ultrasonic' in sensor_lower or 'distance' in sensor_lower:
            return "Distance (cm)", '#198754'  # Green
        elif 'accelerometer' in sensor_lower or 'accel' in sensor_lower:
            return "Acceleration (g)", '#fd7e14'  # Orange
        elif 'vibration' in sensor_lower:
            return "Vibration (units)", '#dc3545'  # Red
        elif 'line' in sensor_lower:
            return "Line Detection", '#6f42c1'  # Purple
        elif 'proximity' in sensor_lower:
            return "Proximity (units)", '#20c997'  # Teal
        elif 'servo' in sensor_lower:
            return "Angle (degrees)", '#ffc107'  # Yellow
        elif 'relay' in sensor_lower:
            return "Relay State", '#6c757d'  # Gray
        elif 'gps' in sensor_lower:
            return "Position", '#0dcaf0'  # Cyan
        else:
            return "Value", '#495057'  # Dark gray default
    
    def _create_empty_graph(self, sensor_name: str) -> go.Figure:
        """Create an empty state graph for inactive sensors."""
        
        fig = go.Figure()
        
        # Add empty scatter to maintain axis structure
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name=sensor_name
        ))
        
        # Add centered text annotation
        fig.add_annotation(
            text="No data available<br><span style='font-size:12px; color:#6c757d;'>Sensor inactive or disconnected</span>",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#adb5bd"),
            align="center"
        )
        
        # Update layout with uirevision to preserve zoom/pan
        fig.update_layout(
            title=dict(
                text=f"{sensor_name} - Offline",
                font=dict(size=14, color='#6c757d'),
                x=0.02,
                xanchor='left'
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                range=[0, 1]
            ),
            yaxis=dict(
                title="Value",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                range=[0, 1]
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.3)',
            paper_bgcolor='white',
            height=300,
            margin=dict(l=60, r=30, t=40, b=50),
            showlegend=False,
            uirevision=f"{sensor_name}-empty"  # Preserve zoom/pan state
        )
        
        return fig
    
    def _create_sensor_info(self, sensor_name: str, data: pd.DataFrame, is_available: bool, field_count: int = 1) -> html.Div:
        """Create sensor info section."""
        if is_available and data is not None:
            # Show current sensor status with field count
            field_text = f"{field_count} data field{'s' if field_count != 1 else ''}"
            return html.Div([
                html.Small([
                    html.I(className="fas fa-circle text-success me-1"),
                    f"Live data ({field_text}) - Last updated: just now"
                ], className="text-muted")
            ])
        else:
            return html.Div([
                html.Small([
                    html.I(className="fas fa-circle text-secondary me-1"),
                    "Sensor offline - No data received"
                ], className="text-muted")
            ])
    
    def _create_fallback_sensor_card(self, sensor_name: str, data: pd.DataFrame, is_available: bool) -> html.Div:
        """Create a fallback sensor card when sensor info is not available."""
        # Use the original single-graph approach
        if is_available and data is not None and not data.empty:
            fig = self._create_sensor_graph(sensor_name, data, "UNKNOWN")
            status = "active"
        else:
            fig = self._create_empty_graph(sensor_name)
            status = "inactive"
        
        from ui.components.common import StatusIndicator
        status_indicator = StatusIndicator.create(status, f"{sensor_name}-status")
        
        return dbc.Card([
            dbc.CardHeader([
                html.H6(sensor_name, className="mb-0 d-inline"),
                html.Div(status_indicator, className="float-end")
            ]),
            dbc.CardBody([
                dcc.Graph(
                    id=f"{sensor_name.replace(' ', '-').lower()}-graph",
                    figure=fig,
                    style={'height': '300px', 'width': '100%'}
                ),
                html.Div(
                    self._create_sensor_info(sensor_name, data, is_available),
                    className="mt-2"
                )
            ])
        ], className="mb-3")
    
    def _create_sensor_field_graph(self, sensor_name: str, field: str, unit: str, sensor_id: str, data: pd.DataFrame = None) -> go.Figure:
        """Create a graph for a specific sensor data field using REAL DATA."""
        
        # Create the plot
        fig = go.Figure()
        
        # Check if we have actual data
        if data is not None and not data.empty and 'Time' in data.columns:
            # Use actual data from the DataFrame
            time_points = data['Time']
            
            # Get the value column (for single-field sensors, it's 'value')
            if 'value' in data.columns:
                values = data['value']
            elif f'value_0' in data.columns:
                values = data[f'value_0']
            else:
                # No data available
                time_points = []
                values = []
            
            if len(values) > 0:
                # Determine color based on field type
                color = self._get_field_color(field)
                
                # Add the trace with REAL data
                fig.add_trace(go.Scatter(
                    x=time_points,
                    y=values,
                    mode='lines+markers',
                    name=f"{field}",
                    line=dict(color=color, width=2),
                    marker=dict(size=4, color=color),
                    hovertemplate=f'<b>{field}</b><br>' +
                                 'Time: %{x}<br>' +
                                 f'Value: %{{y:.2f}} {unit}<br>' +
                                 '<extra></extra>'
                ))
                
                logger.info(f"Plotted {len(values)} real data points for {sensor_name} - {field}")
            else:
                # Show waiting message
                fig.add_annotation(
                    text="Waiting for data...",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="gray"),
                    align="center"
                )
        else:
            # No data available - show empty state
            fig.add_trace(go.Scatter(
                x=[],
                y=[],
                mode='lines',
                name=field
            ))
            
            fig.add_annotation(
                text="Waiting for data...",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="gray"),
                align="center"
            )
        
        # Update layout for professional look with uirevision to preserve zoom/pan
        fig.update_layout(
            title=dict(
                text=f"{sensor_name} - {field.title()}",
                font=dict(size=14, color='#495057'),
                x=0.02,
                xanchor='left'
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='rgba(128, 128, 128, 0.5)',
                tickformat='%H:%M:%S'
            ),
            yaxis=dict(
                title=f"{field.title()} ({unit})" if unit else field.title(),
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linecolor='rgba(128, 128, 128, 0.5)'
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.8)',
            paper_bgcolor='white',
            height=300,
            margin=dict(l=60, r=30, t=40, b=50),
            showlegend=False,
            hovermode='x unified',
            uirevision=f"{sensor_name}-{field}"  # Preserve zoom/pan state
        )
        
        return fig
    
    def _create_empty_field_graph(self, sensor_name: str, field: str, unit: str) -> go.Figure:
        """Create an empty state graph for a specific field."""
        fig = go.Figure()
        
        # Add empty scatter to maintain axis structure
        fig.add_trace(go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name=field
        ))
        
        # Add centered text annotation
        fig.add_annotation(
            text=f"No {field} data available<br><span style='font-size:12px; color:#6c757d;'>Sensor inactive or disconnected</span>",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#adb5bd"),
            align="center"
        )
        
        # Update layout with uirevision to preserve zoom/pan
        fig.update_layout(
            title=dict(
                text=f"{sensor_name} - {field.title()} (Offline)",
                font=dict(size=14, color='#6c757d'),
                x=0.02,
                xanchor='left'
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                range=[0, 1]
            ),
            yaxis=dict(
                title=f"{field.title()} ({unit})" if unit else field.title(),
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showticklabels=False,
                range=[0, 1]
            ),
            plot_bgcolor='rgba(248, 249, 250, 0.3)',
            paper_bgcolor='white',
            height=300,
            margin=dict(l=60, r=30, t=40, b=50),
            showlegend=False,
            uirevision=f"{sensor_name}-{field}-empty"  # Preserve zoom/pan state
        )
        
        return fig
    
    def _generate_field_data(self, field: str, sensor_name: str, sensor_id: str) -> np.ndarray:
        """Generate realistic data for a specific field."""
        # Generate 30 data points
        if field.lower() in ['distance', 'range']:
            # Distance data (5-25 cm for ultrasonic, etc.)
            values = 15 + 8 * np.sin(np.linspace(0, 3*np.pi, 30)) + np.random.normal(0, 0.3, 30)
            return np.clip(values, 2, 30)
        elif field.lower() in ['temperature', 'temp']:
            # Temperature data (20-35�C)
            values = 25 + 5 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 0.5, 30)
            return values
        elif field.lower() in ['pressure']:
            # Pressure data (990-1020 hPa)
            values = 1005 + 10 * np.sin(np.linspace(0, np.pi, 30)) + np.random.normal(0, 1, 30)
            return values
        elif field.lower() in ['acceleration', 'accel', 'x', 'y', 'z']:
            # Acceleration data (-2 to 2 g)
            values = 0.5 * np.sin(np.linspace(0, 4*np.pi, 30)) + np.random.normal(0, 0.1, 30)
            return values
        elif field.lower() in ['vibration', 'amplitude']:
            # Vibration amplitude (0-5)
            values = 2 + 1.5 * np.abs(np.sin(np.linspace(0, 6*np.pi, 30))) + np.random.normal(0, 0.2, 30)
            return np.clip(values, 0, 5)
        elif field.lower() in ['line', 'detection']:
            # Line sensor (0-1 binary + noise)
            base_values = np.random.choice([0, 1], 30, p=[0.7, 0.3])
            return base_values + np.random.normal(0, 0.1, 30)
        elif field.lower() in ['proximity']:
            # Proximity sensor (0-10)
            values = 5 + 3 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 0.3, 30)
            return np.clip(values, 0, 10)
        elif field.lower() in ['angle', 'position']:
            # Servo angle (0-180 degrees)
            values = 90 + 45 * np.sin(np.linspace(0, np.pi, 30)) + np.random.normal(0, 2, 30)
            return np.clip(values, 0, 180)
        elif field.lower() in ['state', 'relay', 'switch']:
            # Relay state (0-1)
            return np.random.choice([0, 1], 30, p=[0.6, 0.4])
        elif field.lower() in ['latitude', 'longitude', 'lat', 'lon']:
            # GPS coordinate change (simulate small movements)
            return np.cumsum(np.random.normal(0, 0.001, 30))
        else:
            # Default generic data
            values = 50 + 20 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 2, 30)
            return values
    
    def _get_field_color(self, field: str) -> str:
        """Get appropriate color for a data field."""
        field_lower = field.lower()
        if field_lower in ['distance', 'range']:
            return '#198754'  # Green
        elif field_lower in ['temperature', 'temp']:
            return '#d63384'  # Pink
        elif field_lower in ['pressure']:
            return '#0d6efd'  # Blue
        elif field_lower in ['acceleration', 'accel', 'x']:
            return '#fd7e14'  # Orange
        elif field_lower in ['y']:
            return '#20c997'  # Teal
        elif field_lower in ['z']:
            return '#6f42c1'  # Purple
        elif field_lower in ['vibration', 'amplitude']:
            return '#dc3545'  # Red
        elif field_lower in ['line', 'detection']:
            return '#6f42c1'  # Purple
        elif field_lower in ['proximity']:
            return '#20c997'  # Teal
        elif field_lower in ['angle', 'position']:
            return '#ffc107'  # Yellow
        elif field_lower in ['state', 'relay', 'switch']:
            return '#6c757d'  # Gray
        elif field_lower in ['latitude', 'lat']:
            return '#0dcaf0'  # Cyan
        elif field_lower in ['longitude', 'lon']:
            return '#198754'  # Green
        else:
            return '#495057'  # Dark gray default
    
    def _register_tcp_console_callback(self, app) -> None:
        """Register TCP console output update callback."""
        @app.callback(
            Output('tcp-console-output', 'children'),
            [Input('sensor-update-interval', 'n_intervals')]
        )
        def update_tcp_console(n_intervals):
            """Update TCP console with recent communication messages."""
            try:
                # Get TCP communication service
                from services.tcp_communication_service import CommunicationService
                tcp_service = container.get(CommunicationService)
                
                # Get recent console messages
                messages = tcp_service.get_console_messages(n=50)
                
                if not messages:
                    return html.Div([
                        html.Div(
                            "No TCP communication data yet...",
                            className="text-muted",
                            style={'fontFamily': 'monospace', 'fontSize': '0.75rem'}
                        )
                    ])
                
                # Keep messages in chronological order (oldest first, newest last)
                
                # Format messages for display
                console_lines = []
                for msg in messages:
                    timestamp = msg['timestamp']
                    direction = msg['direction']
                    message = msg['message']
                    
                    # Determine prefix and color based on direction
                    if direction == 'sent':
                        prefix = 'SEND'
                        color = '#4ec9b0'  # Teal for sent
                    elif direction == 'received':
                        prefix = 'RECV'
                        color = '#569cd6'  # Blue for received
                    elif direction == 'error':
                        prefix = 'ERROR'
                        color = '#f48771'  # Red for errors
                    else:
                        prefix = 'INFO'
                        color = '#dcdcaa'  # Yellow for info
                    
                    # Format JSON for better readability if it's a JSON message
                    display_message = message
                    try:
                        # Try to parse and pretty print JSON
                        if message.startswith('{') or message.startswith('['):
                            parsed = json.loads(message)
                            # Create a compact but readable format
                            msg_type = parsed.get('type', 'unknown')
                            
                            # Simplify display based on message type
                            if msg_type == 'periodic_update':
                                data_count = len(parsed.get('data', []))
                                display_message = f'{{"type": "periodic_update", "data_count": {data_count}}}'
                            elif msg_type == 'get_data':
                                display_message = f'{{"type": "get_data", "request_id": {parsed.get("request_id", "?")}}}'
                            elif msg_type == 'data_response':
                                data_count = len(parsed.get('data', []))
                                display_message = f'{{"type": "data_response", "data_count": {data_count}, "request_id": {parsed.get("request_id", "?")}}}'
                            elif msg_type == 'server_status':
                                serial_conn = parsed.get('serial_connected', False)
                                sensor_count = len(parsed.get('discovered_sensors', []))
                                display_message = f'{{"type": "server_status", "serial_connected": {str(serial_conn).lower()}, "sensors": {sensor_count}}}'
                            else:
                                # For other types, show compact version
                                display_message = json.dumps(parsed, separators=(',', ':'))[:100]
                                if len(json.dumps(parsed)) > 100:
                                    display_message += '...'
                    except:
                        # Not JSON or parsing failed, keep original
                        pass
                    
                    # Create formatted line
                    console_lines.append(
                        html.Div([
                            html.Span(f"{timestamp} ", style={'color': '#858585'}),
                            html.Span(f"[{prefix:5}] ", style={'color': color, 'fontWeight': 'bold'}),
                            html.Span(display_message, style={'color': '#d4d4d4'})
                        ], style={
                            'fontFamily': 'Consolas, Monaco, "Courier New", monospace',
                            'fontSize': '0.75rem',
                            'marginBottom': '2px',
                            'lineHeight': '1.4'
                        })
                    )
                
                # Add a scroll anchor at the end to ensure auto-scroll
                console_lines.append(
                    html.Div(id='console-scroll-anchor', style={'height': '1px'})
                )
                
                # Return with unique key to force update and scroll
                return html.Div([
                    html.Div(console_lines),
                    html.Script(
                        f"""
                        setTimeout(function() {{
                            var console = document.getElementById('tcp-console-output');
                            if (console) {{
                                console.scrollTop = console.scrollHeight;
                            }}
                        }}, 50);
                        """
                    )
                ])
                
            except Exception as e:
                logger.error(f"Error updating TCP console: {e}", exc_info=True)
                return html.Div([
                    html.Div(
                        f"Error loading console: {e}",
                        className="text-danger",
                        style={'fontFamily': 'monospace', 'fontSize': '0.75rem'}
                    )
                ])
