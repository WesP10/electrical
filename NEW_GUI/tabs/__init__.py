# tabs/__init__.py
import os
import importlib
from dash import html, dcc
import dash_bootstrap_components as dbc

def register_tabs(app, sensors):
    tab_modules = get_tab_modules()
    tabs = []
    # Register tab-specific callbacks and collect tabs
    for module in tab_modules:
        tabs.append(dcc.Tab(label=module.tab_label, value=module.tab_id))
        if hasattr(module, 'register_callbacks'):
            module.register_callbacks(app, sensors)
    # Default to the first tab
    default_tab = tab_modules[0].tab_id if tab_modules else None

    # Create the app layout
    app_layout = dbc.Container([
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

    return app_layout

def get_tab_modules():
    tabs_folder = os.path.dirname(__file__)
    tab_modules = []
    for item in os.listdir(tabs_folder):
        item_path = os.path.join(tabs_folder, item)
        if os.path.isdir(item_path) and item != '__pycache__':
            # Try to import the module
            module_name = f'tabs.{item}'
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, 'tab_id') and hasattr(module, 'tab_label') and hasattr(module, 'get_layout'):
                    tab_modules.append(module)
            except Exception as e:
                print(f"Failed to import tab module {module_name}: {e}")
    return tab_modules
