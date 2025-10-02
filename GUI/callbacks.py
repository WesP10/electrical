# callbacks.py
from dash.dependencies import Input, Output
from dash import html
import dash_bootstrap_components as dbc
import tabs

def register_callbacks(app, sensors):
    """
    Register general application callbacks.

    Parameters:
    - app: The Dash app instance.
    - sensors: List of sensor objects.
    """

    # Callback for the Emergency button
    @app.callback(
        Output('emergency-button', 'children'),
        [Input('emergency-button', 'n_clicks')]
    )
    def handle_emergency(n_clicks):
        """
        Handle clicks on the Emergency button.

        Parameters:
        - n_clicks: Number of times the button has been clicked.

        Returns:
        - Updated button label.
        """
        if n_clicks:
            # Placeholder for emergency action
            print("Emergency button clicked!")
            # Implement emergency procedures here
            return "Emergency Activated"
        else:
            return "Emergency"
    
    # Sensor-specific callbacks
    for sensor in sensors:
        if hasattr(sensor, 'register_callbacks'):
            sensor.register_callbacks(app)

    for tab in tabs.get_tab_modules():
        if hasattr(tab, 'register_callbacks'):
            tab.register_callbacks(app, sensors)