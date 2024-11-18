# Sensors Module - README

This document provides an overview of the `sensors` module within the `sensor_dashboard` project. It explains how the sensor system is structured, how to add new sensors, and the expected data format for serial communication to ensure seamless integration with the GUI.

---

## Table of Contents

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Communication Interface](#communication-interface)
  - [PySerialCommunication](#pyserialcommunication)
  - [ZCMCommunication](#zcmcommunication)
- [Adding New Sensors](#adding-new-sensors)
  - [Step 1: Create a New Sensor File](#step-1-create-a-new-sensor-file)
  - [Step 2: Define the Sensor Class](#step-2-define-the-sensor-class)
  - [Step 3: Implement Data Callback (Optional)](#step-3-implement-data-callback-optional)
- [Serial Data Format](#serial-data-format)
  - [Message Structure](#message-structure)
  - [Examples](#examples)
- [Example: Adding a Temperature Sensor](#example-adding-a-temperature-sensor)
- [Closing the Sensor](#closing-the-sensor)
- [Additional Notes](#additional-notes)

---

## Overview

The `sensors` module is designed to manage the integration of various sensors into the Plotly Dash GUI. It handles sensor data acquisition, parsing, and communication between the hardware interface and the GUI components.

---

## Module Structure

The `sensors` directory contains the following files:

- `__init__.py`: Initializes the module and dynamically loads sensor classes.
- `base_sensor.py`: Defines the `BaseSensor` class, which serves as the blueprint for all sensor implementations.
- `communication.py`: Contains communication interfaces (`PySerialCommunication` and `ZCMCommunication`) for interacting with sensors.
- `extra_sensor.py`: Placeholder for additional sensor implementations.
- `load_sensors.py`: Handles the loading of sensor classes (if applicable).

---

## Communication Interface

### PySerialCommunication

This class handles serial communication with sensors connected via serial ports (e.g., USB ports connected to microcontrollers like Arduino).

**Key Features:**

- **Auto-Reconnection**: Attempts to reconnect if the connection is lost.
- **Threaded Reading**: Continuously reads data in a separate thread to prevent blocking the main application.
- **Callback Mechanism**: Uses callbacks to process incoming data for registered sensor IDs.

**Initialization Parameters:**

- `port`: Serial port name (e.g., `COM3`, `/dev/ttyUSB0`).
- `baudrate`: Communication speed (default is `9600`).
- `timeout`: Read timeout in seconds (default is `1`).
- `reconnect_interval`: Time in seconds between reconnection attempts (default is `5`).

### ZCMCommunication

This class manages communication using the ZeroCM (ZCM) library, suitable for networked environments.

**Key Features:**

- **Subscription-Based**: Subscribes to specific channels to receive sensor data.
- **Callback Mechanism**: Processes incoming messages through registered callbacks.
- **Threaded Operation**: Runs the ZCM event loop in a separate thread.

**Initialization Parameters:**

- `url`: The ZCM URL for network communication.
- `channels`: A list of channels to subscribe to for receiving sensor data.

---

## Adding New Sensors

To integrate a new sensor into the system, follow these steps:

### Step 1: Create a New Sensor File

In the `sensors` directory, create a new Python file named `<sensor_name>_sensor.py`. For example, for a temperature sensor, you might name it `temperature_sensor.py`.

### Step 2: Define the Sensor Class

In your new sensor file, define a class named `Sensor` that inherits from `BaseSensor`.

```python
from .base_sensor import BaseSensor

class Sensor(BaseSensor):
    def __init__(self, communication):
        super().__init__(
            name='Temperature Sensor',
            communication=communication,
            sensor_id='TEMP_SENSOR',
            data_fields=['temperature']
        )
```

**Parameters:**

- `name`: A human-readable name for the sensor.
- `communication`: An instance of the communication interface (e.g., `PySerialCommunication`).
- `sensor_id`: A unique identifier string used to distinguish data from this sensor.
- `data_fields`: A list of field names corresponding to the data values sent by the sensor.

### Step 3: Implement Data Callback (Optional)

If your sensor requires custom data processing, you can override the `data_callback` method.

```python
def data_callback(self, values):
    # Custom data processing logic
    pass
```

---

## Serial Data Format

To ensure that the GUI correctly parses the incoming data, sensor data must be sent in a specific format over the serial port.

### Message Structure

```
<sensor_id>:<data_values>
```

- `<sensor_id>`: The unique identifier for the sensor (e.g., `TEMP_SENSOR`).
- `<data_values>`: Comma-separated list of data values (e.g., `23.5`, `0.1,0.2,0.3`).

**Important Notes:**

- **No Extra Spaces**: Do not include spaces in the message.
- **Newline Termination**: Each message should end with a newline character (`\n`).

### Examples

- **Temperature Sensor:**

  ```
  TEMP_SENSOR:23.5
  ```

- **Accelerometer Sensor:**

  ```
  ACCEL_SENSOR:0.1,0.2,0.3
  ```

---

## Example: Adding a Temperature Sensor

1. **Create the Sensor File:**

   Create a file named `temperature_sensor.py` in the `sensors` directory.

2. **Define the Sensor Class:**

   ```python
   from .base_sensor import BaseSensor

   class Sensor(BaseSensor):
       def __init__(self, communication):
           super().__init__(
               name='Temperature Sensor',
               communication=communication,
               sensor_id='TEMP_SENSOR',
               data_fields=['temperature']
           )
   ```

3. **Send Data from the Sensor Hardware:**

   Ensure your sensor hardware sends data in the correct format. For example, from an Arduino:

   ```cpp
   Serial.println("TEMP_SENSOR:23.5");
   ```

   Replace `23.5` with the actual temperature reading.

4. **Data Reception in the GUI:**

   The `PySerialCommunication` class will read this data, and the `BaseSensor`'s `data_callback` method will parse and store it.

---

## Closing the Sensor

When a sensor is no longer needed or the application is shutting down, ensure you properly close the sensor to deregister callbacks and release resources.

```python
sensor.close()
```

---

## Additional Notes

- **Dynamic Sensor Loading:**

  The `sensors/__init__.py` file automatically loads all sensor classes named `Sensor` from files ending with `_sensor.py`. This means you do not need to manually import or register new sensors once you've added the new sensor file and class.

- **Data Handling:**

  - The `BaseSensor` class stores incoming data in `self.data`, which is a list of dictionaries.
  - Use the `get_data()` method to retrieve a Pandas DataFrame of the collected data.
  - Optionally, you can clear the stored data after retrieval by uncommenting `self.data.clear()` in the `get_data()` method.

- **Error Handling:**

  - The system includes basic error handling to manage invalid data and communication errors.
  - Ensure your sensor hardware sends data in the correct format to prevent parsing errors.

- **Thread Safety:**

  - The communication classes use threading and locks to ensure thread safety during read/write operations.
  - Avoid making blocking calls or long-running processes in the `data_callback` method to prevent slowing down the data acquisition thread.

- **Dependencies:**

  - The `PySerialCommunication` class requires the `pyserial` library.
  - The `ZCMCommunication` class requires the `zcm` library.

---

By following this guide, you can seamlessly integrate new sensors into the `sensor_dashboard` project, ensuring that data is correctly captured and displayed in the GUI.

For any further assistance or questions, please refer to the main `README.md` in the project root or contact the development team.