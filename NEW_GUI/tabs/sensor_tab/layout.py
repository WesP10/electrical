# tabs/sensor_tab/layout.py
from dash import html, dcc
import dash_bootstrap_components as dbc

def get_layout(sensors):
    """
    Define the layout for the Sensor Tab.

    Parameters:
    - sensors: List of sensor objects.

    Returns:
    - Dash layout for the Sensor Tab.
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label('Select Sensors:'),
                dcc.Dropdown(
                    id='sensor-dropdown',
                    options=[{'label': sensor.name, 'value': sensor.name} for sensor in sensors],
                    multi=True,
                    value=[sensor.name for sensor in sensors]  # Default to all sensors
                )
            ], width=12, md=6)
        ], className='mb-4'),
        dbc.Row(
            id='sensor-cards',
            children=[]  # Sensor cards will be dynamically inserted here
        )
    ], fluid=True)
