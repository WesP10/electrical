"""
Python environment configuration for the Hyperloop GUI.
This module sets up the Python path and cache directory configuration.
"""
import os
import sys
from pathlib import Path

# Get the project root directory (GUI folder)
# Use PYTHONPATH environment variable if available, otherwise use relative path
if "PYTHONPATH" in os.environ:
    PROJECT_ROOT = Path(os.environ["PYTHONPATH"])
else:
    PROJECT_ROOT = Path(__file__).parent.parent

SRC_DIR = PROJECT_ROOT / "src"

# Set up Python path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Configure centralized cache directory (only if not in container)
if not Path("/.dockerenv").exists():
    CACHE_DIR = PROJECT_ROOT / "__pycache__"
    os.environ["PYTHONPYCACHEPREFIX"] = str(CACHE_DIR)

# Environment variables for the application
ENVIRONMENT_DEFAULTS = {
    "DASH_HOST": "0.0.0.0",  # Docker-friendly default
    "DASH_PORT": "8050",
    "DASH_DEBUG": "false",  # Production-safe default
    "USE_MOCK_COMMUNICATION": "true",  # Default to mock since hardware detection is removed
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