# layout.py
import dash_bootstrap_components as dbc
from dash import html, dcc
from tabs import get_tab_modules  # Function to get tab modules dynamically

def create_layout(sensors):
    # Get the list of tab modules
    tab_modules = get_tab_modules()
    
    # Create tabs dynamically
    tabs = []
    for tab_module in tab_modules:
        tab = dcc.Tab(label=tab_module.tab_label, value=tab_module.tab_id)
        tabs.append(tab)
    
    layout = dbc.Container([
        # Wrap the entire content in a Card for better aesthetics
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
                dcc.Tabs(id='tabs', value=tab_modules[0].tab_id, children=tabs),
                html.Div(id='tabs-content')
            ], fluid=True),
        ], body=True, className="mt-3"),
    ], fluid=True)
    return layout
