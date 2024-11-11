# tabs/__init__.py
import os
import importlib
from dash import html, dcc
from dash.dependencies import Input, Output

def register_tabs(app, sensors):
    """
    Discover tab modules and register their callbacks and layout for use in the app.

    Parameters:
    - app: The Dash app instance.
    - sensors: A list of sensor objects.
    
    Returns:
    - A list of dcc.Tab components for each discovered tab.
    """
    # Discover all tab modules and collect their Tab components
    tab_modules = get_tab_modules()
    tabs = []
    tab_contents = {}
    
    for module in tab_modules:
        # Add a tab component for each discovered module
        tabs.append(dcc.Tab(label=module.tab_label, value=module.tab_id))
        
        # Register each module's specific callbacks if they have them
        if hasattr(module, 'register_callbacks'):
            module.register_callbacks(app, sensors)
        
        # Store each tab's layout function in a dictionary for rendering
        tab_contents[module.tab_id] = module.get_layout(sensors)

    # Set up callback to render content for the selected tab
    @app.callback(
        Output('tabs-content', 'children'),
        [Input('tabs', 'value')]
    )
    def render_tab_content(tab_value):
        """Renders the content of the currently selected tab."""
        return tab_contents.get(tab_value, html.Div('Tab not found'))

    return tabs

def get_tab_modules():
    """
    Discover all valid tab modules within the `tabs/` directory.
    
    Returns:
    - A list of imported tab modules.
    """
    tabs_folder = os.path.dirname(__file__)
    tab_modules = []
    for item in os.listdir(tabs_folder):
        item_path = os.path.join(tabs_folder, item)
        if os.path.isdir(item_path) and item != '__pycache__':
            module_name = f'tabs.{item}'
            try:
                module = importlib.import_module(module_name)
                # Ensure the module has the necessary attributes
                if hasattr(module, 'tab_id') and hasattr(module, 'tab_label') and hasattr(module, 'get_layout'):
                    tab_modules.append(module)
            except Exception as e:
                print(f"Failed to import tab module {module_name}: {e}")
    return tab_modules
