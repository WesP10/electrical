# Cornell Hyperloop GUI - Docker Deployment

## Overview
The GUI has been simplified to use a single Docker-compatible entry point. All device detection and OS-specific launchers have been removed for containerized deployment.

## Entry Point
**Single entry point:** `src/app.py`

### Command Line Options
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

## Docker Deployment

### Build and Run with Docker Compose
```bash
# Production mode
docker-compose -f docker/docker-compose.yml up --build

# Development mode (with hot reload)
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build
```

### Manual Docker Commands
```bash
# Build the image
docker build -f docker/Dockerfile -t hyperloop-gui .

# Run the container
docker run -p 8050:8050 hyperloop-gui
```

## Environment Variables
- `DASH_HOST`: Host to bind to (default: 0.0.0.0)
- `DASH_PORT`: Port to bind to (default: 8050)
- `DASH_DEBUG`: Enable debug mode (default: false)
- `USE_MOCK_COMMUNICATION`: Always true (hardware detection removed)
- `PYTHONPATH`: Set to /app in Docker

## Removed Files
The following files were removed during the cleanup:
- `run.py` - Complex intelligent launcher
- `config/launcher.py` - Python launcher
- `config/run.ps1` - PowerShell launcher
- `config/run.bat` - Batch launcher

## Key Changes
1. **Single Entry Point**: Only `src/app.py` is used
2. **No Device Detection**: Mock communication is the default
3. **Docker-First**: Optimized for containerized deployment
4. **Simplified Configuration**: Environment variable driven
5. **No OS Detection**: Works on any platform via Docker

## Access
Once running, access the GUI at: http://localhost:8050