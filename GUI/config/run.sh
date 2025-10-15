#!/bin/bash
# Shell launcher for the Cornell Hyperloop GUI with centralized Python cache
# This script sets up a centralized __pycache__ directory and launches Python
# Compatible with Linux and macOS

set -e  # Exit on error

# Get the directory where this script is located (config) and go up to GUI root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUI_ROOT="$(dirname "$SCRIPT_DIR")"
CACHE_DIR="$GUI_ROOT/__pycache__"

# Create cache directory if it doesn't exist
if [ ! -d "$CACHE_DIR" ]; then
    mkdir -p "$CACHE_DIR"
    echo "Created centralized cache directory: $CACHE_DIR"
fi

# Set environment variables for centralized cache
export PYTHONPYCACHEPREFIX="$CACHE_DIR"
unset PYTHONDONTWRITEBYTECODE  # Ensure bytecode writing is enabled

# Display configuration
echo "Cornell Hyperloop GUI Launcher"
echo "================================"
echo "Cache Directory: $CACHE_DIR"
echo "PYTHONPYCACHEPREFIX: $PYTHONPYCACHEPREFIX"
echo ""

# Change to GUI directory
cd "$GUI_ROOT"

# Determine which Python to use
if [ -f "../.venv/bin/python" ]; then
    PYTHON_EXEC="../.venv/bin/python"
    echo "Using virtual environment Python: $PYTHON_EXEC"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXEC=".venv/bin/python"
    echo "Using local virtual environment Python: $PYTHON_EXEC"
elif command -v python3 &> /dev/null; then
    PYTHON_EXEC="python3"
    echo "Using system Python3: $PYTHON_EXEC"
elif command -v python &> /dev/null; then
    PYTHON_EXEC="python"
    echo "Using system Python: $PYTHON_EXEC"
else
    echo "Error: No Python interpreter found!"
    echo "Please install Python or activate your virtual environment."
    exit 1
fi

# Launch Python application with all passed arguments
echo "Launching application..."
echo "Command: $PYTHON_EXEC src/app.py $@"
echo ""

if "$PYTHON_EXEC" src/app.py "$@"; then
    EXIT_CODE=$?
    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Application completed successfully."
    else
        echo "Application exited with code: $EXIT_CODE"
    fi
    exit $EXIT_CODE
else
    EXIT_CODE=$?
    echo ""
    echo "Application failed to start or exited with code: $EXIT_CODE"
    exit $EXIT_CODE
fi