# tabs/sensor_tab/sensor_cards/base_sensor_card.py
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import datetime, timedelta

class BaseSensorCard:
    callbacks_registered = {}
    def __init__(self, app, sensor_name, sensor):
        """
        Initialize the base sensor card.

        Parameters:
        - app: The Dash app instance.
        - sensor_name: The name of the sensor.
        - sensor: The sensor object containing data and metadata.
        """
        self.app = app
        self.sensor_name = sensor_name
        self.sensor = sensor
        self.data_fields = sensor.data_fields  # List of data fields (e.g., ['x', 'y', 'z'])

    def create_interval_control(self):
        """
        Create the interval input component.

        Returns:
        - A Div containing the interval control.
        """
        return html.Div([
            html.Label('Update Interval (seconds):'),
            dcc.Input(
                id={'type': 'interval-control', 'sensor_name': self.sensor_name},
                type='number',
                min=1,
                value=5,  # Default interval
                step=1
            ),
        ], className='mb-2')

    def create_time_window_control(self):
        """
        Create the time window input component.

        Returns:
        - A Div containing the time window control.
        """
        return html.Div([
            html.Label('Time Window (seconds):'),
            dcc.Input(
                id={'type': 'time-window', 'sensor_name': self.sensor_name},
                type='number',
                min=0,
                placeholder='All data',
                step=1
            ),
        ], className='mb-2')

    def create_placeholder_graph(self, field):
        """
        Create a placeholder graph for a given data field.

        Parameters:
        - field: The data field name (e.g., 'x', 'temperature').

        Returns:
        - A dcc.Graph component with an empty placeholder figure.
        """
        return dcc.Graph(
            id={'type': 'sensor-graph', 'sensor_name': self.sensor_name, 'field': field},
            figure=go.Figure(
                data=[],
                layout=go.Layout(
                    title=f"{self.sensor_name} - {field.capitalize()}",
                    xaxis={"title": "Time"},
                    yaxis={"title": f"{field.capitalize()} Value"},
                    margin=dict(l=20, r=20, t=30, b=20),
                )
            )
        )

    def create_sensor_content(self):
        """
        Create the sensor content with placeholder graphs for each data field.

        Returns:
        - A Div containing placeholder graphs for each data field.
        """
        graphs = [self.create_placeholder_graph(field) for field in self.data_fields]
        return html.Div(graphs, id={'type': 'sensor-content', 'sensor_name': self.sensor_name})

    def create_sensor_interval(self):
        """
        Create the interval component for periodic updates.

        Returns:
        - A dcc.Interval component.
        """
        return dcc.Interval(
            id={'type': 'sensor-interval', 'sensor_name': self.sensor_name},
            interval=5 * 1000,  # Default interval in milliseconds
            n_intervals=0
        )

    def get_card_body(self):
        """
        Assemble the card body with common components and placeholder graphs.

        Returns:
        - A list of Dash components representing the card body.
        """
        return [
            self.create_interval_control(),
            self.create_time_window_control(),
            self.create_sensor_content(),  # Placeholder graphs for each data field
            self.create_sensor_interval(),
        ]

    def create_card(self):
        """
        Create the complete sensor card.

        Returns:
        - A dbc.Card component representing the sensor card.
        """
        card_body = self.get_card_body()
        card = dbc.Card([
            dbc.CardHeader(html.H5(self.sensor_name)),
            dbc.CardBody(card_body)
        ], 
        className='mb-4',
        id={'type': 'sensor-card', 'sensor_name': self.sensor_name})
        return card

    def register_callbacks(self):
        # Check if callbacks have already been registered for this sensor
        if BaseSensorCard.callbacks_registered.get(self.sensor_name, False):
            BaseSensorCard.callbacks_registered[self.sensor_name] = True
            return
        # if self.app.layout[0].data['callbacks_registered'].get(self.sensor_name, False):
        #     self.app.layout[0].data['callbacks_registered'][self.sensor_name] = True
        #     self.app.layout[0].data
        #     return
        # self.callbacks_registered = True
        # print(self.app.layout[0].data)
        # print(f"Callback registered for {self.sensor_name}")
        # Callback to update the sensor graphs
        @self.app.callback(
            [Output({'type': 'sensor-graph', 'sensor_name': self.sensor_name, 'field': field}, 'figure') for field in self.data_fields],
            Input({'type': 'sensor-interval', 'sensor_name': self.sensor_name}, 'n_intervals'),
            State({'type': 'time-window', 'sensor_name': self.sensor_name}, 'value')
        )
        def update_sensor_graphs(n_intervals, time_window):
            data = self.sensor.get_data()
            # print(data)
            figures = []
            if data.empty:
                # Return empty figures
                for field in self.data_fields:
                    figures.append(go.Figure(
                        layout = {
                            "title":f"{self.sensor_name} - {field.capitalize()}",
                            "xaxis_title":"Time",
                            "yaxis_title":f"{field.capitalize()} Value"
                        }
                    ))
            else:
                # Filter data based on time_window
                if time_window is not None and time_window > 0:
                    cutoff_time = datetime.now() - timedelta(seconds=time_window)
                    data = data[data['Time'] >= cutoff_time]
                for field in self.data_fields:
                    figure = go.Figure(data=[
                        go.Scatter(x=data['Time'], y=data[field], mode='lines', name=field)
                    ])
                    figure.update_layout(
                        title=f"{self.sensor_name} - {field.capitalize()}",
                        xaxis_title="Time",
                        yaxis_title=f"{field.capitalize()} Value"
                    )
                    figures.append(figure)
            return figures

        # Callback to update the interval component's interval property
        @self.app.callback(
            Output({'type': 'sensor-interval', 'sensor_name': self.sensor_name}, 'interval'),
            Input({'type': 'interval-control', 'sensor_name': self.sensor_name}, 'value')
        )
        def update_interval(value):
            if value is None or value < 1:
                return 5 * 1000  # Default interval in milliseconds
            else:
                return int(value * 1000)  # Convert seconds to milliseconds

