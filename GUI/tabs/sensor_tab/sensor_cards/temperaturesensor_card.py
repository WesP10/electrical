# tabs/sensor_tab/sensor_cards/temperaturesensor_card.py
from .base_sensor_card import BaseSensorCard
from ..data_handlers.base_data_handler import BaseSensorDataHandler
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import importlib

class TemperatureSensorCard(BaseSensorCard):
    def __init__(self, app, sensor_name, sensor):
        """
        Initialize the Temperature Sensor card.

        Parameters:
        - app: The Dash app instance.
        - sensor_name: The name of the sensor.
        - sensor: The sensor object containing data and metadata.
        """
        super().__init__(app, sensor_name, sensor)

    def create_unit_control(self):
        """
        Create the temperature unit selection control.

        Returns:
        - A Div containing the temperature unit RadioItems.
        """
        return html.Div([
            html.Label('Temperature Unit:'),
            dbc.RadioItems(
                id={'type': 'temp-unit', 'sensor_name': self.sensor_name},
                options=[
                    {'label': 'Celsius (°C)', 'value': 'C'},
                    {'label': 'Fahrenheit (°F)', 'value': 'F'}
                ],
                value='C',  # Default to Celsius
                inline=True
            )
        ], className='mb-2')

    def get_card_body(self):
        """
        Assemble the card body with common and temperature-specific components.

        Returns:
        - A list of Dash components representing the card body.
        """
        # Get the base card body components
        card_body = super().get_card_body()
        # Insert the temperature unit control after the time window control
        card_body.insert(2, self.create_unit_control())
        return card_body

    def register_callbacks(self):
        """
        Register sensor-specific callbacks for the Temperature Sensor.
        """
        if BaseSensorCard.callbacks_registered.get(self.sensor_name, False):
            BaseSensorCard.callbacks_registered[self.sensor_name] = True
            return
        self.callbacks_registered = True
        @self.app.callback(
            Output({'type': 'sensor-content', 'sensor_name': self.sensor_name}, 'children'),
            [
                Input({'type': 'sensor-interval', 'sensor_name': self.sensor_name}, 'n_intervals'),
                Input({'type': 'time-window', 'sensor_name': self.sensor_name}, 'value'),
                Input({'type': 'temp-unit', 'sensor_name': self.sensor_name}, 'value')
            ],
            [State({'type': 'sensor-content', 'sensor_name': self.sensor_name}, 'id')]
        )
        def update_temperature_sensor_content(n_intervals, time_window_value, temp_unit, content_id):
            """
            Update the Temperature Sensor content based on inputs.

            Parameters:
            - n_intervals: Number of intervals passed.
            - time_window_value: Time window in seconds.
            - temp_unit: Selected temperature unit ('C' or 'F').
            - content_id: The ID of the sensor content component.

            Returns:
            - A list containing the current values display and the graphs.
            """
            sensor_name = content_id['sensor_name']
            sensor = self.sensor
            df = sensor.get_data()

            # Handle default temp_unit if not provided
            if temp_unit is None:
                temp_unit = 'C'  # Default to Celsius

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
            parameters = {'temp_unit': temp_unit}
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
