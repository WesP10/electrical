# app.py
from components import callback_store
from dash import Dash
import dash_bootstrap_components as dbc
from sensors import load_sensors
from sensors.communication import PySerialCommunication  # or ZCMCommunication
from layout import create_layout  # Import the layout function
import callbacks  # Import the general callbacks module
import os
from serial_test import start_sensor_simulation

# Initialize the Dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # Allow callbacks for dynamic components
)
server = app.server

def initialize_app():
    # start_sensor_simulation('loop://', 115200, 10)
    # Initialize shared communication using dependency injection
    communication = PySerialCommunication(
        port='loop://',  # Replace with your serial port
        baudrate=115200,
        timeout=10
    )
    app.layout = [callback_store()]  # Store for general callbacks
    # Load sensors with shared communication
    sensors = load_sensors(communication, app)

    # Assign the main layout of the app
    app.layout.append(create_layout(app, sensors))
    callbacks.register_callbacks(app, sensors)
    # print(app._callback_list)
# Check if the script is run directly (not imported) and if it's the reloader process
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        initialize_app()
    else:
        # Parent process (reloader), do not initialize communication
        pass
    app.run(debug=True)
else:
    # When imported (e.g., by a WSGI server), initialize the app
    initialize_app()
