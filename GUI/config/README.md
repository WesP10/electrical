# Cornell Hyperloop GUI - Configuration & Launchers

This directory contains configuration files and platform-specific launchers for the GUI application.

## Launcher Scripts

The main `run.py` script automatically detects your operating system and uses the appropriate launcher:

### Windows
- **`run.ps1`** - PowerShell launcher (preferred on Windows)
- **`run.bat`** - Batch file launcher (fallback)

### Linux & macOS
- **`run.sh`** - Shell script launcher

### Python Fallback
- **`launcher.py`** - Cross-platform Python launcher (used when OS-specific launchers fail)

## Usage

### Automatic (Recommended)
```bash
# From GUI directory - automatically detects OS and microcontrollers
python run.py
```

### Manual Platform-Specific Launchers

**Windows PowerShell:**
```powershell
# Basic launch
.\config\run.ps1

# With mock communication
.\config\run.ps1 -Mock

# Custom host/port
.\config\run.ps1 -Port 3000 -ServerHost 0.0.0.0
```

**Windows Command Prompt:**
```cmd
config\run.bat
config\run.bat --mock
```

**Linux/macOS:**
```bash
# Make executable (first time only)
chmod +x config/run.sh

# Basic launch
./config/run.sh

# With arguments
./config/run.sh --mock
./config/run.sh --port 3000
```

## Features

All launchers provide:
- **Centralized Python cache** - All `__pycache__` files stored in `GUI/__pycache__/`
- **Virtual environment detection** - Automatically uses `.venv` if available
- **Error handling** - Graceful fallbacks and clear error messages
- **Argument passing** - All command-line arguments passed to the application

## Configuration Files

- **`environment.py`** - Python environment setup and defaults
- **`launcher.py`** - Cross-platform Python launcher implementation
- **`settings.py`** - Application configuration settings
- **`log_config.py`** - Logging configuration

## Troubleshooting

### Linux/macOS Permission Issues
```bash
chmod +x config/run.sh
```

### Virtual Environment Not Detected
Ensure your virtual environment is located at:
- `../venv/` (parent directory)
- `.venv/` (GUI directory)

### PowerShell Execution Policy (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

For more detailed troubleshooting, see the main project documentation.

## Development

When adding new configuration:
1. Update `environment.py` for environment variables
2. Update `settings.py` for application settings
3. Test with all platform launchers
4. Update this README

---

**Cornell Hyperloop Electrical Team** | Configuration & Launchers