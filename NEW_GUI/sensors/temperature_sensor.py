from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name='Temperature Sensor',
            communication=communication,
            sensor_id='TEMP_SENSOR',
            data_fields=['temperature']
        )
