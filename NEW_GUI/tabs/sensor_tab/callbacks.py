# tabs/sensor_tab/callbacks.py
from dash.dependencies import Input, Output, State, MATCH
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from .components import create_sensor_card  # Import from the current tab's components

def register_callbacks(app, sensors):
    sensor_dict = {sensor.name: sensor for sensor in sensors}

    # Callback to generate sensor cards based on selected sensors
    @app.callback(
        Output('sensor-cards', 'children'),
        [Input('sensor-dropdown', 'value')]
    )
    def update_sensor_cards(selected_sensor_names):
        cards = []
        if not selected_sensor_names:
            return cards  # Return empty if no sensors are selected
        for sensor_name in selected_sensor_names:
            sensor = sensor_dict[sensor_name]
            card = create_sensor_card(sensor_name, sensor)
            cards.append(
                dbc.Col(card, width=12, lg=6)
            )
        return cards

    # Callback to update the sensor content when the interval fires
    @app.callback(
        Output({'type': 'sensor-content', 'sensor_name': MATCH}, 'children'),
        [
            Input({'type': 'sensor-interval', 'sensor_name': MATCH}, 'n_intervals'),
            Input({'type': 'time-window', 'sensor_name': MATCH}, 'value'),
        ],
        [State({'type': 'sensor-content', 'sensor_name': MATCH}, 'id')]
    )
    def update_sensor_content(n_intervals, time_window_value, content_id):
        sensor_name = content_id['sensor_name']
        sensor = sensor_dict[sensor_name]
        df = sensor.get_data()

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

        current_values = {}
        graphs = []
        # Create graphs regardless of whether df is empty
        for field in sensor.data_fields:
            fig = go.Figure()
            if not df.empty:
                fig.add_trace(go.Scatter(
                    x=df['Time'],
                    y=df[field],
                    mode='lines',
                    name=field
                ))
            else:
                # Create an empty figure with layout
                fig.add_trace(go.Scatter(
                    x=[], y=[], mode='lines', name=field
                ))
            # Capitalize the first letter of the field name in titles and labels
            field_capitalized = field.capitalize()
            # Use "/" instead of "Over" in the graph titles
            fig.update_layout(
                title=f'{field_capitalized}/Time',
                xaxis_title='Time',
                yaxis_title=field_capitalized,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            graphs.append(dcc.Graph(figure=fig, id=f'{sensor_name}-{field}-graph'))

        # Get the latest values if available
        if not df.empty:
            latest_data = df.iloc[-1]
            for field in sensor.data_fields:
                current_values[field] = latest_data[field]
        else:
            for field in sensor.data_fields:
                current_values[field] = 'N/A'

        # Create current values display with capitalized field names
        current_values_display = html.Div([
            html.H6('Current Values:'),
            html.Ul([html.Li(f'{field.capitalize()}: {value}') for field, value in current_values.items()])
        ])

        # Return the updated content
        return [current_values_display, html.Div(graphs)]

    # Callback to update the interval when the user adjusts the interval control
    @app.callback(
        Output({'type': 'sensor-interval', 'sensor_name': MATCH}, 'interval'),
        [Input({'type': 'interval-control', 'sensor_name': MATCH}, 'value')]
    )
    def update_interval(value):
        try:
            interval_ms = max(1, int(value)) * 1000  # Convert to milliseconds
        except (ValueError, TypeError):
            interval_ms = 5000  # Default to 5 seconds if invalid input
        return interval_ms
