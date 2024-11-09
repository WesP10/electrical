from datetime import datetime
import pandas as pd

class BaseSensor:
    def __init__(self, name, communication, sensor_id, data_fields):
        self.name = name
        self.communication = communication
        self.sensor_id = sensor_id
        self.data_fields = data_fields  # List of field names
        self.data = []
        self.communication.register_callback(self.sensor_id, self.data_callback)

    def data_callback(self, values):
        try:
            data_dict = {'Time': datetime.now()}
            for field_name, value_str in zip(self.data_fields, values):
                data_dict[field_name] = float(value_str)
            self.data.append(data_dict)
        except ValueError as e:
            print(f"Invalid data for {self.sensor_id}: {values} - {e}")

    def get_data(self):
        df = pd.DataFrame(self.data)
        self.data.clear()
        return df

    def close(self):
        self.communication.deregister_callback(self.sensor_id)
