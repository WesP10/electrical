# app.py
import dash
import dash_bootstrap_components as dbc
from sensors import load_sensors
from sensors.communication import PySerialCommunication  # or ZCMCommunication
from layout import create_layout  # Import the layout function
import callbacks  # Import the general callbacks module

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # Allow callbacks for dynamic components
)
server = app.server

# Initialize shared communication using dependency injection
communication = PySerialCommunication(
    port='/dev/ttyUSB0',  # Replace with your serial port
    baudrate=9600,
    timeout=1
)

# Load sensors with shared communication
sensors = load_sensors(communication)

# Assign the main layout of the app
app.layout = create_layout(app, sensors)

# Register general callbacks (Emergency button, etc.)
callbacks.register_callbacks(app, sensors)

if __name__ == '__main__':
    app.run_server(debug=True)
