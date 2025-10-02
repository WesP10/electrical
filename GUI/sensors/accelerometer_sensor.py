from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name='Accelerometer Sensor',
            communication=communication,
            sensor_id='ACCEL_SENSOR',
            data_fields=['x', 'y', 'z']
        )
