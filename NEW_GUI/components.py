# components.py
import dash_bootstrap_components as dbc
from dash import html, dcc

def create_sensor_card(sensor_name, sensor):
    # Interval adjustment control
    interval_control = html.Div([
        html.Label('Update Interval (seconds):'),
        dcc.Input(
            id={'type': 'interval-control', 'sensor_name': sensor_name},
            type='number',
            min=1,
            value=5,  # Default interval
            step=1
        ),
    ], className='mb-2')

    # Sensor-specific Interval component
    sensor_interval = dcc.Interval(
        id={'type': 'sensor-interval', 'sensor_name': sensor_name},
        interval=5 * 1000,  # Default interval in milliseconds
        n_intervals=0
    )

    # Placeholder for dynamic content (current values and graphs)
    sensor_content = html.Div(
        id={'type': 'sensor-content', 'sensor_name': sensor_name}
    )

    card = dbc.Card([
        dbc.CardHeader(html.H5(sensor_name)),
        dbc.CardBody([
            interval_control,
            sensor_content,
            sensor_interval  # Include the Interval component
        ])
    ], className='mb-4')
    return card
