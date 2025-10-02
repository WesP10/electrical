# **Tabs Module README**

Welcome to the **Tabs Module** of the **Sensor Dashboard Application**! This module is responsible for managing the application's tabs, including dynamic discovery, registration, and content rendering. It provides a scalable and modular way to add new functionality to the dashboard without altering the core application code.

---

## **Table of Contents**

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Dynamic Tab Discovery](#dynamic-tab-discovery)
- [Creating a New Tab](#creating-a-new-tab)
  - [1. Create Tab Directory and Files](#1-create-tab-directory-and-files)
  - [2. Define Tab Attributes in `__init__.py`](#2-define-tab-attributes-in-__init__py)
  - [3. Implement `get_layout` Function](#3-implement-get_layout-function)
  - [4. Implement Callbacks (Optional)](#4-implement-callbacks-optional)
- [Tab Callbacks and Content Rendering](#tab-callbacks-and-content-rendering)
- [Example: Sensor Tab](#example-sensor-tab)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## **Overview**

The **Tabs Module** is designed to handle:

- **Dynamic Discovery**: Automatically finding and loading tab modules without manual updates.
- **Callback Management**: Registering tab-specific callbacks and ensuring they do not conflict with general application callbacks.
- **Content Rendering**: Providing the content for each tab based on user interaction.
- **Modularity**: Allowing developers to add new tabs seamlessly by following a standardized structure.

---

## **Module Structure**

```
sensor_dashboard/
├── tabs/
    ├── __init__.py
    ├── sensor_tab/
    │   ├── __init__.py
    │   ├── layout.py
    │   ├── callbacks.py
    │   ├── components.py
    │   ├── data_handlers/
    │   │   ├── __init__.py
    │   │   └── ... (sensor-specific data handlers)
    │   └── sensor_cards/
    │       ├── __init__.py
    │       └── ... (sensor-specific card classes)
    └── another_tab/
        ├── __init__.py
        ├── layout.py
        └── callbacks.py
```

- **`tabs/__init__.py`**: Central module that handles tab discovery and content rendering.
- **`tabs/<tab_name>/`**: Each tab has its own directory containing necessary files.
  - **`__init__.py`**: Defines tab attributes and imports.
  - **`layout.py`**: Contains the `get_layout` function that returns the tab's layout.
  - **`callbacks.py`**: (Optional) Contains tab-specific callbacks.
  - **Additional files and subdirectories** as needed (e.g., components, data handlers).

---

## **Dynamic Tab Discovery**

The Tabs Module uses a dynamic discovery mechanism to automatically find and load tabs. This is handled in `tabs/__init__.py` through the `get_tab_modules` function.

### **How It Works**

- **Directory Scanning**: The `tabs/` directory is scanned for subdirectories (excluding `__pycache__`).
- **Module Importing**: Each subdirectory is treated as a module (e.g., `tabs.sensor_tab`).
- **Attribute Checking**: The module must contain the following attributes:
  - `tab_id`: A unique identifier for the tab.
  - `tab_label`: The label displayed on the tab in the UI.
  - `get_layout`: A function that returns the layout for the tab.

If these conditions are met, the tab is registered and becomes part of the application without any further configuration.

---

## **Creating a New Tab**

Adding a new tab involves creating a new directory within the `tabs/` module and implementing the required files. Follow these steps:

### **1. Create Tab Directory and Files**

Create a new directory under `tabs/` with a name reflecting your tab's purpose.

**Example**: `tabs/your_new_tab/`

**Files to include**:

- `__init__.py`
- `layout.py`
- `callbacks.py` (optional, if your tab requires callbacks)

### **2. Define Tab Attributes in `__init__.py`**

In `tabs/your_new_tab/__init__.py`, define the tab's attributes and import necessary functions.

```python
# tabs/your_new_tab/__init__.py

tab_id = 'your-new-tab'         # Unique identifier for the tab
tab_label = 'Your New Tab'      # Label displayed on the tab

from .layout import get_layout  # Import the layout function

# Optional: Import and register callbacks
from .callbacks import register_callbacks
```

### **3. Implement `get_layout` Function**

In `tabs/your_new_tab/layout.py`, define the `get_layout` function that returns the layout for your tab.

```python
# tabs/your_new_tab/layout.py

from dash import html

def get_layout(sensors):
    return html.Div([
        html.H3('Welcome to Your New Tab'),
        # Add your layout components here
    ])
```

- **Parameters**:
  - `sensors`: List of sensor objects (if needed).
- **Returns**:
  - A Dash layout component.

### **4. Implement Callbacks (Optional)**

If your tab requires specific callbacks, implement them in `callbacks.py`.

```python
# tabs/your_new_tab/callbacks.py

def register_callbacks(app, sensors):
    @app.callback(
        # Define your callback outputs and inputs here
    )
    def your_callback_function():
        # Implement your callback logic
        pass
```

- **`register_callbacks` Function**:
  - Registers all callbacks needed for your tab.
  - Should be called by `tabs/__init__.py` during tab discovery.

---

## **Tab Callbacks and Content Rendering**

### **`tabs/__init__.py` Responsibilities**

- **Registering Tabs**: The `register_tabs` function discovers all tab modules and registers their callbacks and layouts.
- **Rendering Content**: A callback is set up to render the content of the selected tab in the `tabs-content` `Div`.

```python
# tabs/__init__.py (simplified)

def register_tabs(app, sensors):
    tab_modules = get_tab_modules()
    tabs = []
    tab_contents = {}

    for module in tab_modules:
        tabs.append(dcc.Tab(label=module.tab_label, value=module.tab_id))
        if hasattr(module, 'register_callbacks'):
            module.register_callbacks(app, sensors)
        tab_contents[module.tab_id] = module.get_layout(sensors)

    @app.callback(
        Output('tabs-content', 'children'),
        [Input('tabs', 'value')]
    )
    def render_tab_content(tab_value):
        return tab_contents.get(tab_value, html.Div('Tab not found'))

    return tabs
```

- **Callback Registration**: Each tab module's `register_callbacks` function is called if it exists.
- **Content Rendering**: The `render_tab_content` callback updates the `tabs-content` `Div` based on the selected tab.

---

## **Example: Sensor Tab**

The **Sensor Tab** is a practical example of a tab module.

### **Directory Structure**

```
tabs/
└── sensor_tab/
    ├── __init__.py
    ├── layout.py
    ├── callbacks.py
    ├── components.py
    ├── data_handlers/
    │   ├── __init__.py
    │   └── ... (sensor-specific data handlers)
    └── sensor_cards/
        ├── __init__.py
        └── ... (sensor-specific card classes)
```

### **Key Components**

- **`__init__.py`**

  ```python
  # tabs/sensor_tab/__init__.py

  tab_id = 'sensor-tab'
  tab_label = 'Sensors'

  from .layout import get_layout
  from .callbacks import register_callbacks
  ```

- **`layout.py`**

  Defines the layout of the sensor tab, including sensor selection and sensor cards.

  ```python
  # tabs/sensor_tab/layout.py

  from dash import html, dcc
  import dash_bootstrap_components as dbc
  from .components import create_sensor_card

  def get_layout(sensors):
      # Implementation of the layout
      pass
  ```

- **`callbacks.py`**

  Contains callbacks specific to the sensor tab, such as updating sensor cards.

  ```python
  # tabs/sensor_tab/callbacks.py

  def register_callbacks(app, sensors):
      @app.callback(
          # Outputs and Inputs
      )
      def update_sensor_cards():
          # Callback logic
          pass
  ```

- **`components.py`**

  Provides functions to create sensor cards.

  ```python
  # tabs/sensor_tab/components.py

  def create_sensor_card(sensor_name, sensor):
      # Function to create a sensor card
      pass
  ```

---

## **Best Practices**

- **Unique `tab_id` Values**: Ensure each tab has a unique `tab_id` to prevent conflicts.
- **Consistent Naming**: Follow naming conventions for files and classes to facilitate dynamic loading.
- **Modular Design**: Keep tab-specific code within its directory to maintain modularity.
- **Avoid Global Callbacks**: Tab-specific callbacks should not interfere with general application callbacks.
- **Error Handling**: Include exception handling when importing modules to prevent the application from crashing due to a faulty tab.

---

## **Troubleshooting**

### **Tab Not Appearing**

- **Check Directory Structure**: Ensure your tab directory is correctly placed under `tabs/` and not ignored by `.gitignore` or similar.
- **Verify `__init__.py` Attributes**: Confirm that `tab_id`, `tab_label`, and `get_layout` are defined in your tab's `__init__.py`.
- **Inspect Console Output**: Look for import errors or exceptions printed during application startup.

### **Callbacks Not Working**

- **Ensure Callback Registration**: Verify that your tab's `register_callbacks` function is properly defined and imported in `__init__.py`.
- **Check Output and Input IDs**: Make sure the component IDs used in your callbacks match those in your layout.

### **Content Not Updating**

- **Check `render_tab_content` Callback**: Ensure the `tabs-content` callback in `tabs/__init__.py` is correctly returning your tab's layout.
- **Validate Layout Function**: Confirm that `get_layout` returns a valid Dash component.

---

## **Contributing**

Contributions to the Tabs Module are welcome! Please ensure that any additions adhere to the project's modular design principles.

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

Thank you for using and contributing to the **Sensor Dashboard Application**! If you have any questions or need further assistance with the Tabs Module, please feel free to reach out.

---