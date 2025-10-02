# tabs/sensor_tab/data_handlers/accelerometersensor_data_handler.py
from .base_data_handler import BaseSensorDataHandler

class AccelerometerSensorDataHandler(BaseSensorDataHandler):
    def process_data(self, df, parameters=None):
        """
        Process accelerometer data by applying scaling factors to each axis.
        
        Parameters:
        - df (pd.DataFrame): DataFrame containing accelerometer data with columns 
                             ['Time', 'Acceleration_X', 'Acceleration_Y', 'Acceleration_Z'].
        - parameters (dict): Dictionary containing sensor-specific parameters, e.g., 
                             {'scaling_factor': 1.0}.
                             
        Returns:
        - pd.DataFrame: Processed DataFrame with scaled acceleration data.
        """
        if df is not None and not df.empty and parameters:
            scaling_factor = parameters.get('scaling_factor', 1.0)
            # Apply scaling factor to each acceleration axis
            for axis in ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z']:
                if axis in df.columns:
                    df[axis] = df[axis] * scaling_factor
        return df

    def format_current_values(self, latest_data, parameters=None):
        """
        Format the latest acceleration values with appropriate units.
        
        Parameters:
        - latest_data (pd.Series): Series containing the latest accelerometer data.
        - parameters (dict): Dictionary containing sensor-specific parameters, e.g., 
                             {'scaling_factor': 1.0}.
                             
        Returns:
        - dict: Dictionary with formatted current values for display.
        """
        current_values = {}
        for field in self.sensor.data_fields:
            if field.startswith('Acceleration_'):
                value = latest_data[field]
                current_values[field] = f"{value:.2f} m/s²"
            else:
                # For any other fields, return as-is or format accordingly
                current_values[field] = latest_data[field]
        return current_values

    def get_yaxis_title(self, field, parameters=None):
        """
        Get the y-axis title for the acceleration graph, including units.
        
        Parameters:
        - field (str): The data field name (e.g., 'Acceleration_X').
        - parameters (dict): Dictionary containing sensor-specific parameters, e.g., 
                             {'scaling_factor': 1.0}.
                             
        Returns:
        - str: Y-axis title with units.
        """
        if field.startswith('Acceleration_'):
            return "Acceleration (m/s²)"
        return field.capitalize()
