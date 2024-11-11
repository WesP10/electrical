# tabs/sensor_tab/components.py
import importlib
from dash import html, dcc
import dash_bootstrap_components as dbc
from .sensor_cards.base_sensor_card import BaseSensorCard

def create_sensor_card(app, sensor_name, sensor):
    """
    Create a sensor card, dynamically loading sensor-specific classes if available.

    Parameters:
    - app: The Dash app instance.
    - sensor_name: The name of the sensor.
    - sensor: The sensor object containing data and metadata.

    Returns:
    - A Dash Bootstrap Card component representing the sensor.
    """
    # Normalize sensor name to create a valid module/class name
    class_name = sensor_name.replace(' ', '').replace('-', '').replace('_', '')
    module_name = f'tabs.sensor_tab.sensor_cards.{class_name.lower()}_card'
    class_name = f'{class_name}Card'

    try:
        # Dynamically import the module
        module = importlib.import_module(module_name)
        # Get the class from the module
        card_class = getattr(module, class_name)
    except (ImportError, AttributeError):
        # Fallback to the base class if not found
        card_class = BaseSensorCard

    # Instantiate the card class, passing the app instance
    sensor_card = card_class(app, sensor_name, sensor)

    # Register sensor-specific callbacks if applicable
    if hasattr(sensor_card, 'register_callbacks'):
        sensor_card.register_callbacks()

    return sensor_card.create_card()
