# layout.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from tabs import register_tabs  # Import register_tabs to dynamically load tabs

def create_layout(app, sensors):
    """
    Define the main layout of the application, including the Navbar, Emergency button, and tabs.

    Parameters:
    - app: The Dash app instance.
    - sensors: List of sensor objects for the sensor dashboard.

    Returns:
    - A Dash layout component for the main app layout.
    """
    # Register tabs and get a list of dcc.Tab components
    tabs = register_tabs(app, sensors)

    # Ensure we have a default tab if any tabs are available
    default_tab = tabs[0].value if tabs else None

    # Define the main app layout with the Navbar and tab container
    layout = dbc.Container([
        dbc.Card([
            dbc.Navbar(
                dbc.Container([
                    dbc.NavbarBrand("Sensor Dashboard", className="ms-2"),
                    dbc.Button("Emergency", id="emergency-button", color="danger", className="ms-auto"),
                ]),
                color="primary",
                dark=True,
                className="mb-4"
            ),
            dbc.Container([
                dcc.Tabs(id='tabs', value=default_tab, children=tabs),
                html.Div(id='tabs-content')
            ], fluid=True),
        ], body=True, className="mt-3"),
    ], fluid=True)

    return layout
