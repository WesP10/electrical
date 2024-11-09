# tabs/sensor_tab/components.py
from dash import html, dcc
import dash_bootstrap_components as dbc

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

    # Time window control
    time_window_control = html.Div([
        html.Label('Time Window (seconds):'),
        dcc.Input(
            id={'type': 'time-window', 'sensor_name': sensor_name},
            type='number',
            min=0,
            placeholder='All data',
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
            time_window_control,
            sensor_content,
            sensor_interval  # Include the Interval component
        ])
    ], className='mb-4')
    return card
