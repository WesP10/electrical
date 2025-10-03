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

### New Team Members (Intelligent Launcher - Recommended)
**One-command setup with automatic hardware detection:**

```bash
cd GUI
python run.py
```

This intelligent launcher will automatically:
- ✅ **Detect your operating system** (Windows/macOS/Linux)
- ✅ **Scan for connected microcontrollers** (Arduino, ESP32, etc.)
- ✅ **Choose optimal launcher script** (PowerShell/Batch/Shell)
- ✅ **Set up centralized Python cache** (organized `__pycache__`)
- ✅ **Start the dashboard** at `http://localhost:8050`
- ✅ **Use mock data** if no hardware is detected

**See `GUI/SIMPLE_SETUP.md` for detailed setup guide and advanced options.**

### Alternative: Docker Deployment
For containerized deployment or isolated environments:

```bash
cd GUI/docker
./start.bat     # Windows
./start.sh      # macOS/Linux
```

This will:
- Build the Docker container
- Install all dependencies
- Start the dashboard at `http://localhost:8050`

**See `GUI/docker/README.md` for detailed Docker setup guide.**

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

1. **Quick Setup**: See `GUI/SIMPLE_SETUP.md` for one-command setup and troubleshooting
2. **Current Development**: Check `GUI/README.md` for detailed development guides
3. **Architecture Questions**: Review `documentation/` for system diagrams and specs
4. **Legacy Reference**: Browse `depreciated/` for historical implementations
5. **Team Communication**: Contact team leads for project-specific questions

## Contributing

1. **New Features**: Implement in `GUI/` following the modular architecture
2. **Documentation**: Update `documentation/` for any architectural changes
3. **Testing**: Add tests for new functionality
4. **Legacy Code**: Do not modify code in `depreciated/` or `archived_resources/`

## Migration Notes

This repository was restructured in October 2025 to improve maintainability and scalability:

- **Moved Active Code**: NEW_GUI → GUI (current development focus)
- **Preserved Legacy**: Old implementations moved to depreciated/ for reference
- **Organized Documentation**: Centralized in documentation/ folder
- **Archived Resources**: Historical web interfaces preserved in archived_resources/
- **Simplified Setup**: Added intelligent launcher system (`run.py`) for one-command setup
- **Centralized Config**: Moved configuration files to `config/` directory with automatic path resolution

For questions about the restructuring or location of specific files, please contact the electrical team leads.

---

**Cornell Hyperloop Electrical Team** | Last Updated: October 3, 2025
    
