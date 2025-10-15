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

### For New Team Members (Docker - Recommended)
**One-command setup with containerized deployment:**

```bash
cd GUI
docker-compose -f docker/docker-compose.yml up --build
```

The Docker deployment will automatically:
-  **Build the container** with all dependencies
-  **Set up the environment** with proper configuration
-  **Start the dashboard** at `http://localhost:8050`
-  **Use mock data** (no hardware detection needed in containers)
-  **Work on any platform** (Windows/macOS/Linux)

**Having issues? Check the troubleshooting section below or contact the team leads.**

### Docker Deployment (Recommended for Production)
**Single entry point:** `src/app.py`

For containerized deployment or isolated environments:

```bash
# Production mode
cd GUI
docker-compose -f docker/docker-compose.yml up --build

# Development mode (with hot reload)
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build
```

**Manual Docker Commands:**
```bash
# Build the image
cd GUI
docker build -f docker/Dockerfile -t hyperloop-gui .

# Run the container
docker run -p 8050:8050 hyperloop-gui
```

**Docker Environment Variables:**
- `DASH_HOST`: Host to bind to (default: 0.0.0.0)
- `DASH_PORT`: Port to bind to (default: 8050)
- `DASH_DEBUG`: Enable debug mode (default: false)
- `USE_MOCK_COMMUNICATION`: Always true (hardware detection removed)
- `PYTHONPATH`: Set to /app in Docker

**Command Line Options:**
```bash
python src/app.py [options]

Options:
  --debug          Enable debug mode (default: True)
  --no-debug       Disable debug mode
  --host HOST      Host to bind to (default: 0.0.0.0)
  --port PORT      Port to bind to (default: 8050)
  --test           Run tests instead of application
  -h, --help       Show help message
```

### Legacy: Manual Python Setup
```bash
cd GUI
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python src/app.py
```

## Project Structure

The repository has been reorganized into a clean, scalable structure with four main directories:

###  `GUI/` - Active User Interface
**Current Dash-based web application for sensor monitoring and control**
- **Technology**: Python Dash with Bootstrap components
- **Purpose**: Real-time sensor dashboard with modular architecture
- **Key Features**:
  - Dynamic tab management
  - Real-time sensor data visualization
  - Modular sensor cards
  - Emergency controls
  - **Intelligent launcher system** (`run.py`) with automatic hardware detection
  - **Centralized configuration** (`config/` directory)
- **Setup**: See `GUI/SIMPLE_SETUP.md` for quick start guide
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
- **Communication**: PySerial with intelligent mock/hardware detection
- **Data Processing**: Pandas, NumPy
- **Deployment**: Intelligent launcher system + Docker (alternative)
- **Configuration**: Centralized config system with automatic path resolution
- **Development**: Cross-platform launcher scripts (PowerShell/Batch/Shell)

**Legacy Stack (Preserved):**
- **Previous GUI**: PyQt5, PyQtGraph
- **Web Interface**: React, JavaScript
- **Embedded**: Arduino, C/C++

## Getting Help

### Setup Issues
1. **Import Errors**: Run `python GUI/verify_setup.py` to diagnose issues
2. **Common Problems**: See `GUI/SETUP_TROUBLESHOOTING.md` for solutions
3. **Serial Issues**: Check for pyserial vs serial package conflicts

### Development
1. **Current Development**: Check `GUI/README.md` for detailed development guides
2. **Architecture Questions**: Review `documentation/` for system diagrams and specs
3. **Legacy Reference**: Browse `depreciated/` for historical implementations
4. **Team Communication**: Contact team leads for project-specific questions

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
    
