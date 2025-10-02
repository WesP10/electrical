# tabs/sensor_tab/components.py
import importlib
from dash import html, dcc
import dash_bootstrap_components as dbc
from .sensor_cards.base_sensor_card import BaseSensorCard

def get_sensor_card_module(sensor_name):
    """
    Get the sensor card class for the given sensor.

    Parameters:
    - sensor_name: The name of the sensor.
    - sensor: The sensor object containing data and metadata.

    Returns:
    - The sensor card class.
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

    return card_class

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
    card_class = get_sensor_card_module(sensor_name)

    # Instantiate the card class, passing the app instance
    sensor_card = card_class(app, sensor_name, sensor)

    # Register sensor-specific callbacks if not already registered
    
    # sensor_card.register_callbacks() # Uncomment this line to register callbacks (going to try registering outside of individual cards)

    return sensor_card.create_card()

def create_all_sensor_cards(app, sensors):
    """
    Create all sensor cards and register their callbacks.

    Parameters:
    - app: The Dash app instance.
    - sensors: List of sensor objects.

    Returns:
    - A dictionary mapping sensor names to their card components.
    """
    sensor_cards = []
    for sensor in sensors:
        sensor_name = sensor.name
        # Create the sensor card
        card = create_sensor_card(app, sensor_name, sensor)
        sensor_cards.append(card)
    return sensor_cards