# tabs/sensor_tab/data_handlers/temperaturesensor_data_handler.py
from .base_data_handler import BaseSensorDataHandler

class TemperatureSensorDataHandler(BaseSensorDataHandler):
    def process_data(self, df, parameters=None):
        """
        Process temperature data based on the selected unit.

        Parameters:
        - df: Pandas DataFrame containing sensor data.
        - parameters: Dictionary containing 'temp_unit'.

        Returns:
        - Processed DataFrame with temperature converted if needed.
        """
        if df is not None and not df.empty and parameters:
            temp_unit = parameters.get('temp_unit', 'C')
            if temp_unit == 'F':
                # Convert Celsius to Fahrenheit
                df['Temperature'] = df['Temperature'] * 9 / 5 + 32
        return df

    def format_current_values(self, latest_data, parameters=None):
        """
        Format the current temperature value with the appropriate unit.

        Parameters:
        - latest_data: Pandas Series containing the latest sensor data.
        - parameters: Dictionary containing 'temp_unit'.

        Returns:
        - Dictionary of formatted current values.
        """
        current_values = {}
        if parameters:
            temp_unit = parameters.get('temp_unit', 'C')
        else:
            temp_unit = 'C'
        unit = '°F' if temp_unit == 'F' else '°C'
        for field in self.sensor.data_fields:
            if field == 'Temperature':
                value = latest_data[field]
                current_values[field] = f"{value:.2f} {unit}"
            else:
                current_values[field] = latest_data[field]
        return current_values

    def get_yaxis_title(self, field, parameters=None):
        """
        Get the y-axis title for the Temperature graph, including the unit.

        Parameters:
        - field: The data field name.
        - parameters: Dictionary containing 'temp_unit'.

        Returns:
        - String representing the y-axis title with unit.
        """
        if parameters:
            temp_unit = parameters.get('temp_unit', 'C')
        else:
            temp_unit = 'C'
        unit = '°F' if temp_unit == 'F' else '°C'
        if field == 'Temperature':
            return f"Temperature ({unit})"
        return field.capitalize()
