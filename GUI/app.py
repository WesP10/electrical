# app.py
from components import callback_store
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from sensors import load_sensors
from sensors.communication import PySerialCommunication  # or ZCMCommunication
from layout import create_layout  # Import the layout function
import callbacks  # Import the general callbacks module
import os
from serial_test import start_sensor_simulation
from dash.dependencies import Output, Input

# Initialize the Dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # Allow callbacks for dynamic components
)
server = app.server

# Initialize shared communication using dependency injection
def get_serial_communication():
    try:
        return PySerialCommunication(
            port='loop://',  # Replace with your serial port, e.g., 'COM3'
            baudrate=115200,
            timeout=100
        )
    except Exception as e:
        print(f"Error initializing serial communication: {e}")
        # Fall back to mock communication for development/testing
        try:
            from sensors.mock_communication import MockCommunication
            print("Using mock communication for development/testing")
            return MockCommunication()
        except Exception as mock_error:
            print(f"Error initializing mock communication: {mock_error}")
            return None

def initialize_app():
    print("Initializing Cornell Hyperloop GUI...")
    
    # Initialize communication
    communication = get_serial_communication()
    if not communication:
        print("Communication could not be initialized. Running without sensors.")
        sensors = []
    else:
        # Initialize sensors
        sensors = load_sensors(communication, app)
        print(f"Loaded {len(sensors)} sensors: {[s.name for s in sensors]}")
    
    # Initialize the app layout
    app.layout = html.Div([
        callback_store(),
        dcc.Tabs([
            dcc.Tab(label='Main Tab', children=create_layout(app, sensors)),
            dcc.Tab(label='Profiles', children=create_profile_tab())
        ])
    ])
    
    # Register callbacks
    callbacks.register_callbacks(app, sensors)
    print("App initialization complete!")

def create_profile_tab():
    return dbc.Container(
        [
            html.Div(
                [
                    html.H2("Select Profile", className="text-center mb-4"),
                    dbc.Button("Pre Acceleration", id="profile-1", color="primary", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Acceleration", id="profile-2", color="primary", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Cruise", id="profile-3", color="success", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Deacceleration", id="profile-4", color="warning", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Crawl", id="profile-5", color="warning", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Stop", id="profile-6", color="warning", className="mb-2", style={"width": "100%"}),
                    dbc.Button("Emergency", id="profile-7", color="danger", className="mb-2", style={"width": "100%"}),
                    html.Div(id="profile-output", className="mt-4 text-center"),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "height": "100vh",
                },
            )
        ],
        fluid=True,
        className="d-flex align-items-center justify-content-center",
    )

# Button callbacks
@app.callback(
    Output('profile-output', 'children'),
    [Input('profile-1', 'n_clicks'),
     Input('profile-2', 'n_clicks'),
     Input('profile-3', 'n_clicks'),
     Input('profile-4', 'n_clicks'),
     Input('profile-5', 'n_clicks'),
     Input('profile-6', 'n_clicks'),
     Input('profile-7', 'n_clicks')]
)
def handle_profile_buttons(profile1, profile2, profile3, profile4, profile5, profile6, profile7):
    # Get communication object
    communication = get_serial_communication()
    if not communication:
        return "Arduino not connected!"

    ctx = dcc.callback_context
    if not ctx.triggered:
        return "No profile selected yet!"
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Map button ID to Arduino command
    profile_map = {
        'profile-1': '1',
        'profile-2': '2',
        'profile-3': '3',
        'profile-4': '4',
        'profile-5': '5',
        'profile-6': '6',
        'profile-7': '7',
    }
    command = profile_map.get(button_id)

    # Send command to Arduino
    try:
        if command and communication:
            communication.send_command(command)  # Assuming PySerialCommunication has a send_command method
            return f"Switched to {button_id.capitalize()}!"
    except Exception as e:
        print(f"Failed to send command: {e}")
    return "Failed to send command."

# Initialize the app before running
initialize_app()

# Check if the script is run directly (not imported)
if __name__ == '__main__':
    # Get host and port from environment variables for Docker compatibility
    host = os.environ.get('DASH_HOST', '127.0.0.1')
    port = int(os.environ.get('DASH_PORT', '8050'))
    debug = os.environ.get('DASH_DEBUG', 'true').lower() == 'true'
    
    print(f"Starting server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)