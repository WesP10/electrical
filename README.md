# Cornell Hyperloop - Electrical Team Repository

This repository contains the electrical team's code, documentation, and resources for the Cornell Hyperloop project.

### Current Team Members
* **Aislinn Ennis**: Electrical Lead
* **Weston Clark**: ECC Lead
* **Lalo Esparza**: Power Systems Lead

#### ECC Team
* Weston Clark, Jordan Zeiger, Prayga Babbar
#### Power Systems Team  
* Lalo Esparza, Tribeca Kao


## Quick Start

### Option 1: Docker (Recommended)
**Simple setup with containerized deployment:**

```bash
# Start Docker GUI (sensors will show "No Hardware" without serial server)
cd GUI
docker-compose -f docker/docker-compose.yml up --build
# Access at: http://localhost:8050
```

### Universal Serial Setup (Works on Windows/Mac/Linux)

***Start Universal Serial Server with Flags**
```bash
# Auto-detect and connect to Arduino/microcontroller
cd GUI
python src/services/serial_server.py --auto-detect

# Interactive selection from detected devices
python src/services/serial_server.py --interactive

# Manual port specification (if needed)
python src/services/serial_server.py --port YOUR_PORT --baudrate 115200
```

**Step 2: Start Docker GUI**
```bash
cd docker
# From docker directory
docker-compose up --build
# Access at: http://localhost:8050
```
## Docker Setup with Serial Port Access

Since Docker containers cannot directly access host serial ports, we use a **serial server bridge** architecture for hardware connectivity:

```
Host System (Windows/Mac/Linux)
├── Serial Port (Arduino/Microcontroller)
├── Serial Server (Python) ── TCP Port 9999
└── Docker Container (GUI) ── Connects to TCP Port 9999
```

### Auto-Detection Features

The serial server automatically detects microcontrollers with confidence scoring:

- **HIGH Confidence**: Arduino Uno, ESP32, ESP8266 with proper VID/PID
- **MEDIUM Confidence**: CH340, CP210x, FTDI USB-to-serial adapters  
- **LOW Confidence**: Generic serial devices and USB converters

**Universal Port Detection:**
- **Windows**: COM3, COM4, COM5, COM6, etc.
- **macOS**: `/dev/tty.usbmodem*`, `/dev/tty.usbserial*`
- **Linux**: `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.

**No platform-specific scripts needed** - PySerial handles all OS differences automatically!

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERIAL_SERVER_MODE` | Enable TCP serial server mode | `true` |
| `SERIAL_SERVER_HOST` | Serial server hostname | `127.0.0.1` |
| `SERIAL_SERVER_PORT` | Serial server TCP port | `9999` |
| `DASH_HOST` | GUI host binding | `0.0.0.0` |
| `DASH_PORT` | GUI port | `8050` |
| `DASH_DEBUG` | Enable debug mode | `false` |

### Supported Devices

The system automatically detects:
- Arduino Uno, Nano, Mega
- ESP32, ESP8266
- CH340, CP210x, FTDI USB-to-serial chips
- Generic COM/USB serial devices

## Project Structure

The repository has been reorganized into a clean, scalable structure with four main directories:

###  `GUI/` - Active User Interface
**Current Dash-based web application for sensor monitoring and control**

```
GUI/
├── src/                          # Main application code
│   ├── app.py                   # Application entry point
│   ├── core/                    # Core application logic
│   ├── services/                # Communication & data services
│   │   └── serial_server.py     # Universal serial server with auto-detection
│   ├── ui/                      # User interface components
│   └── utils/                   # Utility functions
├── config/                      # Configuration files
├── docker/                      # Docker configuration
└── requirements.txt             # Python dependencies
```

- **Technology**: Python Dash with Bootstrap components
- **Purpose**: Real-time sensor dashboard with modular architecture
- **Key Features**:
  - Real-time sensor monitoring with live data visualization
  - Cross-platform support (Windows, macOS, Linux)
  - Docker deployment with containerized setup
  - Hardware detection with automatic Arduino/microcontroller discovery
  - Modular architecture for easy sensor extension
  - Web interface with modern, responsive dashboard
  - Serial communication with robust port handling
- **Status**: Active development

### `documentation/` - Project Documentation
**All current documentation, diagrams, and technical specs**
- `Diagrams/` - System architecture and wiring diagrams
- `docs/` - Technical documentation
- PDF documents and specifications
- **Status**: Current documentation

### `depreciated/` - Legacy Code (Preserved for Reference)
**Older implementations that are no longer actively maintained**
- `Communications/` - ZCM communication protocol implementation
- `Sensors/` - Legacy sensor libraries and Arduino code
- `State_Estimation/` - State machine and estimation algorithms
- `Old/` - Previous software versions and implementations
- `zcm testing/` - Communication protocol testing
- **Status**: Preserved for reference, not actively maintained

### `archived_resources/` - Historical Resources
**Legacy web interfaces and learning materials**
- `Website/` - Previous React-based web interface
- `WebsiteTemplate/` - React template and components
- `Workshop/` - Tutorial and learning code
- **Status**: Archived for historical reference

## Development Guidelines

### Adding New Features
- **GUI Components**: Add to `GUI/` following the modular architecture
- **Documentation**: Add to `documentation/` with clear organization
- **Testing**: Include appropriate tests for new functionality

### Working with Legacy Code
- **Reference Only**: Code in `depreciated/` should only be referenced, not modified
- **Migration**: When updating legacy features, implement in `GUI/` or appropriate active directory
- **Documentation**: Update documentation when migrating functionality

## Project Status

| Component | Status | Description |
|-----------|--------|-------------|
| GUI Dashboard | Active | Modern Dash-based interface |
| Sensor Integration | In Progress | Migrating from legacy implementations & adding new sensors |
| Communication Protocol | Legacy | ZCM implementation in depreciated |
| Documentation | Legacy | Now use Confluence |

## Technology Stack

**Current Active Stack:**
- **Frontend**: Python Dash, Dash Bootstrap Components, Plotly
- **Communication**: PySerial with universal auto-detection across all platforms
- **Data Processing**: Pandas, NumPy
- **Deployment**: Docker with serial server bridge architecture
- **Configuration**: Centralized config system with automatic path resolution
- **Development**: Universal serial server with intelligent device detection

**Legacy Stack (Preserved):**
- **Previous GUI**: PyQt5, PyQtGraph
- **Web Interface**: React, JavaScript
- **Embedded**: Arduino, C/C++

## Development

### Local Development Setup

```bash
# Clone and navigate
cd GUI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python -m src.app --debug
```

### Development with Hardware

```bash
# Terminal 1: Start universal serial server
python src/services/serial_server.py --auto-detect
# or for interactive selection:
python src/services/serial_server.py --interactive

# Terminal 2: Run GUI locally
SERIAL_SERVER_MODE=true SERIAL_SERVER_HOST=localhost python -m src.app
```

## Troubleshooting

### GUI Shows "No Hardware" Despite Connected Device

1. **Check Serial Server**: Look for "Successfully connected to PORT" message
2. **Verify Port**: Ensure no other software is using the serial port
3. **Docker Network**: Test `curl http://host.docker.internal:9999` from container
4. **Permissions**: Check port permissions and driver installation

### Serial Server Issues

1. **Install PySerial**: `pip install pyserial`
2. **Check Available Ports**: 
   ```python
   python -c "import serial.tools.list_ports; [print(f'{p.device} - {p.description}') for p in serial.tools.list_ports.comports()]"
   ```
3. **Port In Use**: Close Arduino IDE, PuTTY, or other serial monitors

### Docker Connection Issues

1. **Windows**: Ensure using `host.docker.internal`
2. **Firewall**: Allow Python through firewall for port 9999
3. **Network Mode**: Try `network_mode: "host"` in compose file

## Common Device Settings

| Device | Typical Port | Baud Rate |
|--------|--------------|-----------|
| Arduino Uno | COM3-COM6 (Win) / /dev/ttyACM0 (Linux) | 115200 |
| ESP32 | COM4-COM8 (Win) / /dev/ttyUSB0 (Linux) | 115200 |
| Arduino Nano | COM3-COM6 (Win) / /dev/ttyUSB0 (Linux) | 57600 |
| Generic Serial | Various | 9600 |

## Getting Help

### Setup Issues
1. **Import Errors**: Check Python environment and dependencies
2. **Serial Issues**: Verify pyserial installation and port permissions
3. **Docker Issues**: Check container logs and network connectivity

### Development
1. **Architecture Questions**: Review `documentation/` for system diagrams and specs
2. **Legacy Reference**: Browse `depreciated/` for historical implementations
3. **Team Communication**: Contact team leads for project-specific questions

## Contributing

1. **New Features**: Implement in `GUI/` following the modular architecture
2. **Documentation**: Update `documentation/` for any architectural changes
3. **Testing**: Add tests for new functionality
4. **Legacy Code**: Do not modify code in `depreciated/` or `archived_resources/`

## Docker Deployment Notes

The GUI has been optimized for Docker deployment with the following changes:

**Key Docker Changes:**
1. **Single Entry Point**: Only `src/app.py` is used (no complex launchers in Docker)
2. **No Device Detection**: Mock communication is the default in containers
3. **Docker-First**: Optimized for containerized deployment
4. **Simplified Configuration**: Environment variable driven
5. **No OS Detection**: Works on any platform via Docker

**Removed Files (Docker Cleanup):**
- `run.py` - Complex intelligent launcher (replaced by Docker entry point)
- `config/launcher.py` - Python launcher
- `config/run.ps1` - PowerShell launcher
- `config/run.bat` - Batch launcher
- `config/run.sh` - Shell launcher script
- `serial_server.log` - Old log file
- `**/__pycache__/` - Python bytecode cache directories

## Migration Notes

This repository was restructured in October 2025 to improve maintainability and scalability:

- **Moved Active Code**: NEW_GUI → GUI (current development focus)
- **Preserved Legacy**: Old implementations moved to depreciated/ for reference
- **Organized Documentation**: Centralized in documentation/ folder
- **Archived Resources**: Historical web interfaces preserved in archived_resources/
- **Docker Optimization**: Simplified entry point system for containerized deployment
- **Centralized Config**: Essential configuration files in `config/` directory

For questions about the restructuring or location of specific files, please contact the electrical team leads.

---

**Cornell Hyperloop Electrical Team** | Last Updated: October 3, 2025
    
