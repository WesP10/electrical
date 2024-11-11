# tabs/sensor_tab/sensor_cards/accelerometersensor_card.py
from .base_sensor_card import BaseSensorCard
from ..data_handlers.base_data_handler import BaseSensorDataHandler
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import importlib

class AccelerometerSensorCard(BaseSensorCard):
    def __init__(self, app, sensor_name, sensor):
        super().__init__(app, sensor_name, sensor)

    def register_callbacks(self):
        @self.app.callback(
            Output({'type': 'sensor-content', 'sensor_name': MATCH}, 'children'),
            [
                Input({'type': 'sensor-interval', 'sensor_name': MATCH}, 'n_intervals'),
                Input({'type': 'time-window', 'sensor_name': MATCH}, 'value')
            ],
            [State({'type': 'sensor-content', 'sensor_name': MATCH}, 'id')]
        )
        def update_accelerometer_sensor_content(n_intervals, time_window_value, content_id):
            """
            Update the Accelerometer Sensor content based on inputs.

            Parameters:
            - n_intervals: Number of intervals passed.
            - time_window_value: Time window in seconds.
            - content_id: The ID of the sensor content component.

            Returns:
            - A list containing the current values display and the graphs.
            """
            sensor_name = content_id['sensor_name']
            sensor = self.sensor
            df = sensor.get_data()

            # No additional parameters for Accelerometer Sensor
            parameters = {}

            # Filter the data based on the time window if provided
            if time_window_value is not None and df is not None and not df.empty:
                try:
                    time_window_seconds = float(time_window_value)
                    if time_window_seconds > 0:
                        current_time = datetime.now()
                        time_threshold = current_time - timedelta(seconds=time_window_seconds)
                        df['Time'] = pd.to_datetime(df['Time'])
                        df = df[df['Time'] >= time_threshold]
                except (ValueError, TypeError):
                    pass  # If conversion fails, show all data

            # Dynamically load the data handler class
            class_name = sensor_name.replace(' ', '').replace('-', '').replace('_', '')
            module_name = f'tabs.sensor_tab.data_handlers.{class_name.lower()}_data_handler'
            class_name = f'{class_name}DataHandler'

            try:
                module = importlib.import_module(module_name)
                data_handler_class = getattr(module, class_name)
            except (ImportError, AttributeError):
                data_handler_class = BaseSensorDataHandler

            data_handler = data_handler_class(sensor_name, sensor)

            # Process data with sensor-specific parameters
            df = data_handler.process_data(df, parameters=parameters)

            # Prepare current values
            if not df.empty:
                latest_data = df.iloc[-1]
                current_values = data_handler.format_current_values(latest_data, parameters=parameters)
            else:
                current_values = {field: 'N/A' for field in sensor.data_fields}

            # Generate graphs
            graphs = []
            for field in sensor.data_fields:
                if field == 'Time':
                    continue  # Skip plotting the Time field itself
                fig = go.Figure()
                if not df.empty:
                    fig.add_trace(go.Scatter(
                        x=df['Time'],
                        y=df[field],
                        mode='lines',
                        name=field
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=[], y=[], mode='lines', name=field
                    ))
                # Get y-axis title from data handler
                yaxis_title = data_handler.get_yaxis_title(field, parameters=parameters)
                # Update figure layout
                fig.update_layout(
                    title=f'{field.capitalize()} Over Time',
                    xaxis_title='Time',
                    yaxis_title=yaxis_title,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                graphs.append(dcc.Graph(figure=fig, id=f'{sensor_name}-{field}-graph'))

            # Create current values display
            current_values_display = html.Div([
                html.H6('Current Values:'),
                html.Ul([html.Li(f'{field.capitalize()}: {value}') for field, value in current_values.items()])
            ])

            return [current_values_display, html.Div(graphs)]
