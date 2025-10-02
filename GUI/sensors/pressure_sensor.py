from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name='Pressure Sensor',
            communication=communication,
            sensor_id='PRESSURE_SENSOR',
            data_fields=['pressure']
        )
