# tabs/sensor_tab/layout.py
from dash import html, dcc
import dash_bootstrap_components as dbc

def get_layout(sensors):
    sensor_names = [sensor.name for sensor in sensors]

    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.Label('Select Sensors to Display'),
                dcc.Dropdown(
                    id='sensor-dropdown',
                    options=[{'label': name, 'value': name} for name in sensor_names],
                    value=sensor_names,  # Default to all sensors selected
                    multi=True,
                    clearable=False
                ),
            ], width=12),
        ]),
        html.Br(),
        dbc.Row(
            id='sensor-cards',
            # Children will be generated in the callback
        )
    ])
    return layout
