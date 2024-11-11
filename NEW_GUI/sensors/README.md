# **Sensors Module README**

Welcome to the **Sensors Module** of the **Sensor Dashboard Application**! This module is responsible for managing sensor interactions, including communication, data retrieval, and sensor initialization. It provides a structured way to integrate various sensors into the application, ensuring scalability and maintainability.

---

## **Table of Contents**

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Communication Classes](#communication-classes)
- [Creating a New Sensor](#creating-a-new-sensor)
  - [1. Create Sensor Class](#1-create-sensor-class)
  - [2. Update `load_sensors` Function](#2-update-load_sensors-function)
- [Sensor Class Guidelines](#sensor-class-guidelines)
- [Example: Temperature Sensor](#example-temperature-sensor)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## **Overview**

The **Sensors Module** is designed to:

- **Facilitate Sensor Integration**: Provide a standardized way to add new sensors.
- **Manage Communication**: Handle communication protocols (e.g., serial communication).
- **Support Data Retrieval**: Define methods for fetching sensor data.
- **Promote Modularity**: Allow sensors to be added or removed without affecting other parts of the application.

---

## **Module Structure**

```
sensor_dashboard/
├── sensors/
    ├── __init__.py
    ├── communication.py
    ├── load_sensors.py
    ├── base_sensor.py
    ├── temperature_sensor.py
    ├── accelerometer_sensor.py
    └── ... (other sensor classes)
```

- **`communication.py`**: Defines communication classes used by sensors.
- **`load_sensors.py`**: Contains the `load_sensors` function to initialize all sensors.
- **`base_sensor.py`**: Provides a base class for sensors to inherit common functionality.
- **`<sensor_name>_sensor.py`**: Individual sensor classes implementing specific sensor logic.

---

## **Communication Classes**

The module includes communication classes to abstract the details of how sensors communicate with the application.

### **Available Communication Classes**

- **`PySerialCommunication`**

  - **File**: `communication.py`
  - **Description**: Handles serial communication using the `pyserial` library.
  - **Usage**:

    ```python
    from sensors.communication import PySerialCommunication

    communication = PySerialCommunication(
        port='/dev/ttyUSB0',  # Replace with your serial port
        baudrate=9600,
        timeout=1
    )
    ```

- **`ZCMCommunication`**

  - **File**: `communication.py`
  - **Description**: Placeholder for ZeroMQ or ZCM communication implementation.
  - **Usage**:

    ```python
    from sensors.communication import ZCMCommunication

    communication = ZCMCommunication(
        address='tcp://localhost:5555',  # Replace with your ZCM address
    )
    ```

### **Implementing Custom Communication**

If you need to implement a new communication protocol:

1. **Create a New Class in `communication.py`**

   ```python
   class YourCommunicationClass:
       def __init__(self, ...):
           # Initialize communication parameters
           pass

       def read(self):
           # Implement data reading logic
           pass

       def write(self, data):
           # Implement data writing logic
           pass
   ```

2. **Use Your Communication Class When Initializing Sensors**

   ```python
   communication = YourCommunicationClass(...)
   ```

---

## **Creating a New Sensor**

To add a new sensor to the application, follow these steps:

### **1. Create Sensor Class**

Create a new sensor class in the `sensors/` directory, following the naming convention `<sensor_name>_sensor.py`.

**Example**: `sensors/your_sensor.py`

```python
# sensors/your_sensor.py

from .base_sensor import BaseSensor

class YourSensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(communication)
        self.name = "Your Sensor Name"
        self.data_fields = ['field1', 'field2']  # List of data fields provided by the sensor

    def get_data(self):
        # Implement data retrieval logic
        # Should return a dictionary or Pandas DataFrame with data_fields as keys/columns
        data = {
            'Time': datetime.now(),
            'field1': ...,
            'field2': ...,
        }
        return data
```

### **2. Update `load_sensors` Function**

Add your new sensor class to the list of sensors in `load_sensors.py`.

```python
# sensors/load_sensors.py

from .your_sensor import YourSensor

def load_sensors(communication):
    sensors = [
        YourSensor(communication),
        # ... other sensors
    ]
    return sensors
```

---

## **Sensor Class Guidelines**

When creating a sensor class, adhere to the following guidelines:

- **Inherit from `BaseSensor`**: This ensures consistency and allows you to leverage common functionality.
- **Define `self.name`**: A unique name for the sensor.
- **Define `self.data_fields`**: A list of data fields the sensor provides (excluding 'Time').
- **Implement `get_data` Method**:

  - Should return a dictionary or a Pandas DataFrame containing the sensor data.
  - Must include a 'Time' field with a timestamp.
  - Keys or columns should match `self.data_fields`.

- **Handle Exceptions**: Ensure that any communication errors are handled gracefully.

**Example**:

```python
# sensors/base_sensor.py

from datetime import datetime

class BaseSensor:
    def __init__(self, communication):
        self.communication = communication

    def get_data(self):
        raise NotImplementedError("get_data method must be implemented by subclasses.")
```

---

## **Example: Temperature Sensor**

Here's how the Temperature Sensor is implemented:

**File**: `sensors/temperature_sensor.py`

```python
# sensors/temperature_sensor.py

from .base_sensor import BaseSensor
from datetime import datetime

class TemperatureSensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(communication)
        self.name = "Temperature Sensor"
        self.data_fields = ['Temperature']

    def get_data(self):
        # Simulate reading temperature data
        temperature = self.read_temperature()
        data = {
            'Time': datetime.now(),
            'Temperature': temperature,
        }
        return data

    def read_temperature(self):
        # Implement the logic to read temperature from the sensor
        # For example, parse data from self.communication.read()
        return 25.0  # Placeholder value
```

**Explanation**:

- **Inheritance**: Inherits from `BaseSensor`.
- **Sensor Name and Data Fields**: Sets `self.name` and `self.data_fields`.
- **Data Retrieval**: Implements `get_data` to return a dictionary with 'Time' and 'Temperature'.
- **Reading Data**: Includes a `read_temperature` method to encapsulate sensor-specific reading logic.

---

## **Best Practices**

- **Modular Design**: Keep sensor-specific logic within its class.
- **Consistent Data Format**: Ensure `get_data` returns data in a consistent format.
- **Error Handling**: Catch exceptions during data retrieval and handle them appropriately.
- **Documentation**: Comment your code to explain the purpose of methods and any complex logic.
- **Reusability**: Use helper methods for repeated tasks within the sensor class.

---

## **Troubleshooting**

### **Sensor Data Not Appearing**

- **Check Communication**: Ensure that the communication interface is correctly configured and the sensor is connected.
- **Verify `get_data` Implementation**: Confirm that `get_data` is returning data in the expected format.
- **Inspect Logs**: Look for any error messages printed to the console.

### **Application Crashes When Adding New Sensor**

- **Syntax Errors**: Ensure there are no syntax errors in your sensor class.
- **Proper Inheritance**: Confirm that your sensor class inherits from `BaseSensor`.
- **Update `load_sensors`**: Make sure you've added your sensor to the `load_sensors` function.

### **Sensor Data Fields Not Displayed Correctly**

- **Data Field Names**: Ensure that `self.data_fields` matches the keys in the data returned by `get_data`.
- **Consistent Naming**: Use consistent and descriptive names for data fields.

---

## **Contributing**

Contributions to the Sensors Module are welcome! Please ensure that any additions adhere to the project's modular design principles.

### **Steps to Contribute**

1. **Fork the Repository**

   ```bash
   git clone https://github.com/yourusername/sensor_dashboard.git
   ```

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make Changes and Commit**

   ```bash
   git add .
   git commit -m "Add your feature"
   ```

4. **Push to Your Fork and Submit a Pull Request**

   ```bash
   git push origin feature/your-feature
   ```

---

## **License**

This project is licensed under the MIT License.

---

Thank you for using and contributing to the **Sensor Dashboard Application**! If you have any questions or need further assistance with the Sensors Module, please feel free to reach out.

---

**Note**: When adding new sensors, consider whether you also need to create a corresponding **Data Handler** in `tabs/sensor_tab/data_handlers/` to process and format the sensor data for display. This ensures consistency in how data is presented in the dashboard.

---