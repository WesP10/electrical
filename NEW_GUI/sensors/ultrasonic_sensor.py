from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name='Ultrasonic Sensor',
            communication=communication,
            sensor_id='ULSO_SENSOR',
            data_fields=['distance']
        )