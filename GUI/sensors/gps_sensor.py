from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name="GPS Sensor",
            communication=communication,
            sensor_id="GPS_SENSOR",
            data_fields=["latitude", "longitude", "altitude"]
        )
