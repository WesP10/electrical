import os
import importlib
from .base_sensor import BaseSensor

def load_sensors(communication):
    sensors = []
    sensor_folder = os.path.dirname(__file__)
    for filename in os.listdir(sensor_folder):
        if filename.endswith('_sensor.py') and filename != 'base_sensor.py':
            module_name = f'sensors.{filename[:-3]}'
            module = importlib.import_module(module_name)
            sensor_class = getattr(module, 'Sensor', None)
            if sensor_class and issubclass(sensor_class, BaseSensor):
                sensors.append(sensor_class(communication))
    return sensors
