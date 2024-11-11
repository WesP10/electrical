# tabs/sensor_tab/data_handlers/base_data_handler.py

class BaseSensorDataHandler:
    def __init__(self, sensor_name, sensor):
        """
        Initialize the base sensor data handler.

        Parameters:
        - sensor_name: The name of the sensor.
        - sensor: The sensor object containing data and metadata.
        """
        self.sensor_name = sensor_name
        self.sensor = sensor

    def process_data(self, df, parameters=None):
        """
        Process the sensor data.

        Parameters:
        - df: Pandas DataFrame containing sensor data.
        - parameters: Dictionary of sensor-specific parameters.

        Returns:
        - Processed DataFrame.
        """
        # General data processing (if any)
        return df

    def format_current_values(self, latest_data, parameters=None):
        """
        Format the current sensor values for display.

        Parameters:
        - latest_data: Pandas Series containing the latest sensor data.
        - parameters: Dictionary of sensor-specific parameters.

        Returns:
        - Dictionary of formatted current values.
        """
        current_values = {}
        for field in self.sensor.data_fields:
            current_values[field] = latest_data[field]
        return current_values

    def get_yaxis_title(self, field, parameters=None):
        """
        Get the y-axis title for a given field.

        Parameters:
        - field: The data field name.
        - parameters: Dictionary of sensor-specific parameters.

        Returns:
        - String representing the y-axis title.
        """
        # Default y-axis title
        return field.capitalize()
