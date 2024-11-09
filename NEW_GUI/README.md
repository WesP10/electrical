# Sensor Dashboard Application

Welcome to the **Sensor Dashboard Application**! This application provides a dynamic and modular web interface for monitoring and visualizing data from various sensors. It is built using Python's Dash framework and leverages a modular design to facilitate easy maintenance and extension.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Navigating the Dashboard](#navigating-the-dashboard)
  - [Interacting with Sensors](#interacting-with-sensors)
  - [Adding New Tabs](#adding-new-tabs)
- [Customization](#customization)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

The Sensor Dashboard Application allows users to monitor real-time data from multiple sensors. It provides an interactive interface where users can:

- View graphs of sensor data over time.
- Adjust the update interval for each sensor.
- Specify the time window of data to display on the graphs.
- Select which sensors to display.
- Easily add new tabs and functionalities to the dashboard.

---

## Features

- **Modular Design**: Each tab in the dashboard is self-contained, with its own layout, components, and callbacks, making the application highly extensible.
- **Real-Time Data Visualization**: Graphs update at user-defined intervals, displaying live sensor data.
- **Customizable Time Window**: Users can specify how much historical data to display for each sensor.
- **Sensor Selection**: Users can choose which sensors to display on the dashboard.
- **Emergency Button**: A placeholder for implementing emergency procedures.
- **Responsive UI**: Built with Dash Bootstrap Components for a responsive and modern user interface.

---

## Prerequisites

- **Python 3.7 or higher**
- **Pip package manager**
- **Sensors and Communication Interface**: Physical sensors connected via serial port or a mock setup for testing.

---

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/sensor-dashboard.git
   cd sensor-dashboard
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Serial Port (If Using Physical Sensors)**

   - In `app.py`, update the `PySerialCommunication` parameters with the correct `port` and `baudrate` for your setup.

     ```python
     communication = PySerialCommunication(
         port='/dev/ttyUSB0',  # Replace with your serial port
         baudrate=9600,
         timeout=1
     )
     ```

---

## Project Structure

```
sensor-dashboard/
├── app.py
├── tabs/
│   ├── __init__.py
│   ├── base_tab.py
│   ├── sensor_tab/
│   │   ├── __init__.py
│   │   ├── layout.py
│   │   ├── callbacks.py
│   │   └── components.py
│   └── another_tab/  # Example of additional tab
│       ├── __init__.py
│       ├── layout.py
│       ├── callbacks.py
│       └── components.py
├── sensors/
│   ├── __init__.py
│   ├── base_sensor.py
│   ├── communication.py
│   ├── temperature_sensor.py
│   ├── pressure_sensor.py
│   └── accelerometer_sensor.py
├── callbacks.py
├── requirements.txt
└── README.md
```

**Explanation**:

- **app.py**: The main application file that initializes the Dash app and sets up the layout.
- **tabs/**: Contains subdirectories for each tab, encapsulating their layouts, components, and callbacks.
  - **__init__.py**: Initializes the tabs module and provides functions to register tabs.
  - **base_tab.py**: Defines the base structure for tab modules.
  - **sensor_tab/**: Contains code specific to the Sensors tab.
    - **__init__.py**: Sets up the tab's identity and imports.
    - **layout.py**: Defines the layout of the sensor tab.
    - **callbacks.py**: Contains callbacks specific to the sensor tab.
    - **components.py**: Contains components used in the sensor tab.
- **sensors/**: Contains sensor classes and communication interfaces.
  - **base_sensor.py**: Defines the base sensor class.
  - **communication.py**: Handles communication with sensors (e.g., serial communication).
  - **temperature_sensor.py**, **pressure_sensor.py**, **accelerometer_sensor.py**: Specific sensor implementations.
- **callbacks.py**: Contains overall project-level callbacks.
- **requirements.txt**: Lists all Python dependencies.
- **README.md**: Documentation for the project.

---

## Usage

### Running the Application

To start the application, navigate to the project directory and run:

```bash
python app.py
```

The application will start a local server, typically at `http://127.0.0.1:8050/`. Open this URL in your web browser to view the dashboard.

### Navigating the Dashboard

- **Tabs**: The dashboard includes multiple tabs for organizing different functionalities.
  - **Sensors**: The main tab for monitoring sensor data.
  - **Additional Tabs**: Any other tabs you've added (e.g., status, settings).

- **Emergency Button**: Located in the navigation bar, this button is a placeholder for implementing emergency procedures.

### Interacting with Sensors

- **Sensor Selection**: Use the dropdown at the top of the Sensors tab to select which sensors to display.

- **Sensor Cards**: Each selected sensor appears as a card containing:
  - **Update Interval**: Input to set how frequently the sensor data and graphs update (in seconds).
  - **Time Window**: Input to specify how much historical data to display on the graphs (in seconds).
    - Leave this blank to display all available data.
  - **Current Values**: Displays the most recent readings from the sensor.
  - **Graphs**: Plots of sensor data over time.

- **Adjusting Update Intervals**:
  - Enter a positive integer to set the update interval for the sensor.
  - The graphs and data will refresh at this interval.

- **Specifying Time Window**:
  - Enter the number of seconds to view data from that time period up to the present.
  - For example, entering `60` will display the last 60 seconds of data.

### Adding New Tabs

The application is designed to make adding new tabs straightforward.

#### Steps to Add a New Tab:

1. **Create a New Directory** in the `tabs/` folder:

   ```
   tabs/
   └── your_new_tab/
       ├── __init__.py
       ├── layout.py
       ├── callbacks.py
       └── components.py
   ```

2. **Define Tab Identity in `__init__.py`**:

   ```python
   # tabs/your_new_tab/__init__.py
   from .layout import get_layout
   from .callbacks import register_callbacks

   tab_id = 'your-new-tab-id'
   tab_label = 'Your New Tab Label'
   ```

3. **Implement the Layout in `layout.py`**:

   ```python
   # tabs/your_new_tab/layout.py
   from dash import html

   def get_layout(sensors):
       layout = html.Div([
           html.H3('Content for Your New Tab'),
           # Add your components here
       ])
       return layout
   ```

4. **Implement Callbacks in `callbacks.py`**:

   ```python
   # tabs/your_new_tab/callbacks.py

   def register_callbacks(app, sensors):
       # Add callbacks specific to your new tab
       pass
   ```

5. **Implement Components in `components.py`** (Optional):

   ```python
   # tabs/your_new_tab/components.py
   from dash import html

   # Define any custom components for your tab
   ```

6. **Restart the Application**:

   ```bash
   python app.py
   ```

   The new tab should now appear in the dashboard.

---

## Customization

- **Sensors**:
  - **Adding New Sensors**: Implement new sensor classes in the `sensors/` directory, following the pattern of existing sensors.
  - **Sensor Communication**: Customize the `communication.py` file if you need to change how sensors communicate with the application.

- **Styling**:
  - **Themes**: The application uses Dash Bootstrap Components. You can change the theme by modifying the `external_stylesheets` parameter in `app.py`.
  - **Custom CSS**: Add custom CSS files to the `assets/` directory for further styling.

- **Graphs**:
  - Modify graph appearances by adjusting the Plotly `go.Figure` configurations in the callbacks.

- **Emergency Button**:
  - Implement the desired functionality for the emergency button in `callbacks.py`.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**.
2. **Create a New Branch** for your feature or bug fix.
3. **Make Your Changes**.
4. **Submit a Pull Request** with a detailed description of your changes.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

Thank you for using the Sensor Dashboard Application! If you have any questions or need assistance, please feel free to reach out.

---

# Additional Notes

- **Data Handling**: The application uses Pandas data frames to handle sensor data. Ensure that your sensors provide data in a compatible format.
- **Error Handling**: The application includes basic error handling. You may enhance it to suit your needs.
- **Performance**: For a large number of sensors or high-frequency updates, consider optimizing data retrieval and update mechanisms.
- **Security**: If deploying the application in a production environment, ensure appropriate security measures are in place.