"""
Python environment configuration for the Hyperloop GUI.
This module sets up the Python path and cache directory configuration.
"""
import os
import sys
from pathlib import Path

# Get the project root directory (GUI folder)
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"

# Set up Python path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Configure centralized cache directory
CACHE_DIR = PROJECT_ROOT / "__pycache__"
os.environ["PYTHONPYCACHEPREFIX"] = str(CACHE_DIR)

# Environment variables for the application
ENVIRONMENT_DEFAULTS = {
    "DASH_HOST": "127.0.0.1",
    "DASH_PORT": "8050",
    "DASH_DEBUG": "true",
    "USE_MOCK_COMMUNICATION": "false",
    "SERIAL_PORT": "loop://",
    "SERIAL_BAUDRATE": "115200",
    "SERIAL_TIMEOUT": "100",
    "APP_TITLE": "Cornell Hyperloop Sensor Dashboard"
}

def setup_environment():
    """Set up environment variables with defaults."""
    for key, default_value in ENVIRONMENT_DEFAULTS.items():
        if key not in os.environ:
            os.environ[key] = default_value

def get_project_root():
    """Get the project root directory."""
    return PROJECT_ROOT

def get_src_dir():
    """Get the source directory."""
    return SRC_DIR

if __name__ == "__main__":
    setup_environment()
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Source directory: {SRC_DIR}")
    print(f"Cache directory: {CACHE_DIR}")
    print("Environment configured successfully!")