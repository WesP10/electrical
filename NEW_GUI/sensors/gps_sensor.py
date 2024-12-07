from .base_sensor import BaseSensor


class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name="GPS Sensor",
            communication=communication,
            sensor_id="GPS_SENSOR",
            data_fields=["latitude", "longitude", "altitude"],
        )


def parse_data(self, raw_data):
    """
    Parses raw GPS data (e.g., NMEA format or custom string).
    Assumes data comes in the form: 'lat=<value>,lon=<value>,alt=<value>'
    """
    try:
        match = re.match(
            r"lat=([-+]?\d*\.\d+|\d+),lon=([-+]?\d*\.\d+|\d+),alt=([-+]?\d*\.\d+|\d+)",
            raw_data,
        )
        if match:
            latitude, longitude, altitude = match.groups()
            return {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "altitude": float(altitude),
            }
        else:
            raise ValueError("Invalid data format")
    except Exception as e:
        print(f"Error parsing GPS data: {e}")
        return None
