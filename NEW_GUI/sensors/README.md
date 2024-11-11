# **Sensors Module README**

Welcome to the **Sensors Module** of the **Sensor Dashboard Application**! This module is responsible for managing sensor interactions, including communication, data retrieval, and sensor initialization. It provides a structured way to integrate various sensors into the application, ensuring scalability and maintainability.

---

## **Table of Contents**

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Communication Classes](#communication-classes)
  - [PySerial Communication](#pyserial-communication)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Configuring Serial Communication](#configuring-serial-communication)
    - [Example: Reading Data from Arduino](#example-reading-data-from-arduino)
  - [Arduino Data Format](#arduino-data-format)
    - [Expected Data Format](#expected-data-format)
    - [Sample Arduino Code](#sample-arduino-code)
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
- **Manage Communication**: Handle communication protocols (e.g., serial communication with Arduino).
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

### **PySerial Communication**

**PySerial** is a Python library that encapsulates the access for the serial port. It provides backends for Python running on Windows, Linux, and other platforms.

#### **Installation**

To use PySerial, you need to install it using pip:

```bash
pip install pyserial
```

#### **Usage**

**File**: `sensors/communication.py`

```python
import serial

class PySerialCommunication:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        Initialize serial communication.

        Parameters:
        - port (str): Serial port name (e.g., '/dev/ttyUSB0' on Linux or 'COM3' on Windows).
        - baudrate (int): Communication speed.
        - timeout (float): Read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.serial_connection = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            print(f"Connected to serial port {self.port}")
        except serial.SerialException as e:
            print(f"Error connecting to serial port {self.port}: {e}")
            self.serial_connection = None

    def read_line(self):
        """
        Read a line from the serial port.

        Returns:
        - str: Decoded line from the serial port.
        """
        if self.serial_connection and self.serial_connection.in_waiting:
            line = self.serial_connection.readline()
            return line.decode('utf-8').strip()
        return None

    def write(self, data):
        """
        Write data to the serial port.

        Parameters:
        - data (str): Data to send.
        """
        if self.serial_connection:
            self.serial_connection.write(data.encode('utf-8'))
```

#### **Configuring Serial Communication**

When initializing `PySerialCommunication`, you need to provide the correct serial port and parameters.

**Example Initialization in `app.py`:**

```python
# app.py
from sensors.communication import PySerialCommunication

# Initialize shared communication using dependency injection
communication = PySerialCommunication(
    port='/dev/ttyUSB0',  # Replace with your serial port (e.g., 'COM3' on Windows)
    baudrate=9600,        # Ensure this matches the Arduino's baud rate
    timeout=1
)
```

**Determining the Serial Port:**

- **Linux/Mac**: Serial ports are usually named `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.
- **Windows**: Serial ports are named `COM1`, `COM2`, etc.

#### **Example: Reading Data from Arduino**

In your sensor class, you can use the `read_line` method to get data from the Arduino.

```python
# sensors/your_sensor.py

from .base_sensor import BaseSensor
from datetime import datetime

class YourSensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(communication)
        self.name = "Your Sensor Name"
        self.data_fields = ['Temperature', 'Humidity']

    def get_data(self):
        line = self.communication.read_line()
        if line:
            # Parse the line into data
            data = self.parse_data(line)
            if data:
                data['Time'] = datetime.now()
                return data
        return None

    def parse_data(self, line):
        # Implement parsing logic based on the expected data format
        pass
```

---

## **Arduino Data Format**

To ensure proper communication between the Arduino and the application, the data sent from the Arduino must be in a format that the Python application can parse.

### **Expected Data Format**

The data format should be:

- **Consistent**: Each line sent over serial should follow the same structure.
- **Parsable**: Use a format that's easy to parse in Python (e.g., CSV, JSON).

**Common Formats:**

1. **Comma-Separated Values (CSV):**

   ```
   value1,value2,value3
   ```

2. **JSON String:**

   ```
   {"Temperature":25.0,"Humidity":40.0}
   ```

3. **Key-Value Pairs:**

   ```
   Temperature=25.0;Humidity=40.0
   ```

### **Sample Arduino Code**

Below is an example Arduino sketch that sends sensor data in CSV format over serial.

**Example:**

```cpp
// Arduino Sketch

void setup() {
  Serial.begin(9600); // Set the baud rate to match PySerialCommunication
}

void loop() {
  // Read sensor values
  float temperature = readTemperatureSensor();
  float humidity = readHumiditySensor();

  // Send data over serial in CSV format
  Serial.print(temperature);
  Serial.print(",");
  Serial.println(humidity);

  delay(1000); // Send data every second
}

float readTemperatureSensor() {
  // Replace with actual sensor reading code
  return 25.0;
}

float readHumiditySensor() {
  // Replace with actual sensor reading code
  return 40.0;
}
```

**Notes:**

- The Arduino sends data in the format: `25.0,40.0`
- Each data line is terminated with a newline character `\n`, which `readline()` in PySerial uses to read the complete line.

---

## **Creating a New Sensor**

To add a new sensor to the application, follow these steps:

### **1. Create Sensor Class**

Create a new sensor class in the `sensors/` directory, following the naming convention `<sensor_name>_sensor.py`.

**Example**: `sensors/your_sensor.py`

```python
# sensors/your_sensor.py

from .base_sensor import BaseSensor
from datetime import datetime

class YourSensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(communication)
        self.name = "Your Sensor Name"
        self.data_fields = ['Temperature', 'Humidity']

    def get_data(self):
        line = self.communication.read_line()
        if line:
            data = self.parse_data(line)
            if data:
                data['Time'] = datetime.now()
                return data
        return None

    def parse_data(self, line):
        try:
            # Assuming CSV format: Temperature,Humidity
            values = line.split(',')
            if len(values) == 2:
                temperature = float(values[0])
                humidity = float(values[1])
                return {
                    'Temperature': temperature,
                    'Humidity': humidity
                }
        except ValueError as e:
            print(f"Error parsing line '{line}': {e}")
        return None
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

  - Should return a dictionary containing the sensor data.
  - Must include a 'Time' field with a timestamp.
  - Keys should match `self.data_fields`.

- **Implement `parse_data` Method**:

  - Parse the line read from the serial port into a dictionary.

- **Handle Exceptions**: Ensure that any communication errors are handled gracefully.

**Example**:

```python
# sensors/base_sensor.py

class BaseSensor:
    def __init__(self, communication):
        self.communication = communication

    def get_data(self):
        raise NotImplementedError("get_data method must be implemented by subclasses.")
```

---

## **Example: Temperature Sensor**

Here's how the Temperature Sensor is implemented, using PySerial communication and parsing data from the Arduino.

**Arduino Sketch (Sending Data):**

```cpp
// Arduino Sketch for Temperature Sensor

void setup() {
  Serial.begin(9600);
}

void loop() {
  float temperature = readTemperatureSensor();
  Serial.println(temperature); // Send temperature value
  delay(1000);
}

float readTemperatureSensor() {
  // Replace with actual sensor reading code
  return 25.0;
}
```

**Python Sensor Class:**

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
        line = self.communication.read_line()
        if line:
            data = self.parse_data(line)
            if data:
                data['Time'] = datetime.now()
                return data
        return None

    def parse_data(self, line):
        try:
            temperature = float(line)
            return {'Temperature': temperature}
        except ValueError as e:
            print(f"Error parsing temperature '{line}': {e}")
            return None
```

---

## **Best Practices**

- **Match Baud Rates**: Ensure that the baud rate set in the Arduino sketch (`Serial.begin(baudrate)`) matches the baud rate specified in `PySerialCommunication`.
- **Consistent Data Format**: Keep the data format consistent and simple to parse.
- **Data Validation**: Validate data in the `parse_data` method to handle any anomalies.
- **Logging**: Print informative messages when errors occur to facilitate debugging.
- **Resource Management**: Close serial connections properly when the application exits.

---

## **Troubleshooting**

### **No Data Received from Arduino**

- **Check Serial Port**: Verify the correct serial port is used.
- **Baud Rate Mismatch**: Ensure baud rates match between Arduino and PySerial.
- **Arduino Not Sending Data**: Confirm that the Arduino is powered and running the correct sketch.
- **Permissions**: On Unix systems, you may need to add your user to the `dialout` group or run the application with elevated permissions.

### **Data Parsing Errors**

- **Incorrect Data Format**: Ensure the data sent from the Arduino matches the expected format in the `parse_data` method.
- **Error Messages**: Review any error messages printed during parsing to identify issues.

### **Serial Connection Errors**

- **Port Already in Use**: Close other programs that might be using the serial port (e.g., Arduino IDE Serial Monitor).
- **SerialException**: Check for exceptions when initializing `PySerialCommunication`.

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