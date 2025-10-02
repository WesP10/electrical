# Docker Setup for Cornell Hyperloop GUI

This folder contains all Docker-related files for the Cornell Hyperloop sensor dashboard. Docker provides a consistent, automated environment that eliminates setup headaches for new team members.

## Quick Start for New Team Members

### Prerequisites
- **Docker Desktop** (the ONLY thing you need to install)
  - [Windows](https://www.docker.com/products/docker-desktop)
  - [macOS](https://www.docker.com/products/docker-desktop)
  - [Linux](https://docs.docker.com/engine/install/)

### One-Command Setup

**Windows:**
```bash
cd electrical/GUI/docker
./start.bat
```

**macOS/Linux:**
```bash
cd electrical/GUI/docker
chmod +x start.sh
./start.sh
```

That's it! The dashboard will be running at `http://localhost:8050`

## Files in This Directory

- **`Dockerfile`** - Container build configuration
- **`docker-compose.yml`** - Main service configuration
- **`docker-compose.dev.yml`** - Development overrides
- **`Makefile`** - Convenient command shortcuts
- **`start.bat`** - Windows automated setup script
- **`start.sh`** - macOS/Linux automated setup script
- **`README.md`** - This documentation

## Development Workflow

### Making Code Changes

1. **Start in development mode** (with live reload):
   ```bash
   make dev
   # OR
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   ```

2. **Edit code** in your favorite editor
3. **Save changes** - they're automatically reflected in the browser
4. **Test** at `http://localhost:8050`

### Useful Commands

```bash
# Using Makefile (recommended)
make help          # Show all available commands
make build         # Build the Docker image
make up            # Start the application
make down          # Stop the application
make restart       # Restart the application
make logs          # View application logs
make clean         # Remove containers and images
make dev           # Development mode with live reload
make prod          # Production mode

# Using Docker Compose directly
docker-compose build                    # Build image
docker-compose up -d                    # Start in background
docker-compose down                     # Stop and remove containers
docker-compose logs -f hyperloop-gui    # Follow logs
docker-compose restart                  # Restart services
```

## Configuration

### Development vs Production

**Development Mode (`make dev`):**
- Live code reloading
- Debug mode enabled
- Volume mounting (local code → container)
- Better error messages

**Production Mode (`make prod`):**
- Optimized performance
- Secure configuration
- Code built into image
- Production logging

### Environment Variables

Key environment variables (set in `docker-compose.yml`):
- `DASH_HOST=0.0.0.0` - Listen on all interfaces
- `DASH_PORT=8050` - Application port
- `DASH_DEBUG=false` - Debug mode (true in dev)
- `PYTHONPATH=/app` - Python module path

### Ports

- **8050** - Main application port
- Exposed as `localhost:8050` on your machine

## Troubleshooting

### Common Issues

**Docker not running:**
```bash
# Start Docker Desktop and ensure it's running
docker info  # Should not error
```

**Port conflicts:**
```bash
# Change port in docker-compose.yml if 8050 is busy
ports:
  - "8051:8050"  # Use 8051 instead
```

**Build failures:**
```bash
# Clean Docker cache and rebuild
docker system prune -f
make clean
make build
```

**Permission issues (Linux/macOS):**
```bash
# Make scripts executable
chmod +x start.sh

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Then log out and log back in
```

**Application won't start:**
```bash
# Check logs for errors
make logs

# Start fresh
make clean
make up
```

### Getting Help

1. **Check logs**: `make logs` or `docker-compose logs -f`
2. **Restart fresh**: `make clean && make up`
3. **Ask the team**: Post in electrical team chat
4. **GitHub Issues**: Create issue in repository

## Why Docker?

### Benefits for Team Members
- **No Python setup**: Same Python 3.11 for everyone
- **No dependency conflicts**: All packages pre-installed
- **Consistent environment**: Works on Windows, macOS, Linux
- **Quick onboarding**: Productive in minutes
- **Easy updates**: Pull new image, restart

### Benefits for Development
- **Isolated environment**: No system pollution
- **Reproducible builds**: Same everywhere
- **Easy deployment**: Same container → production
- **Team consistency**: Everyone runs identical setup

## Technical Details

### Container Architecture

```
┌─────────────────────────────────────┐
│ Cornell Hyperloop GUI Container     │
├─────────────────────────────────────┤
│ Python 3.11 + Dependencies         │
│ ├── Dash + Bootstrap Components     │
│ ├── Plotly for visualization        │
│ ├── PySerial for sensor data        │
│ └── All requirements.txt packages   │
├─────────────────────────────────────┤
│ Security: Non-root user             │
│ Health checks: Built-in monitoring  │
│ Port: 8050                          │
└─────────────────────────────────────┘
```

### File Structure Impact

```
GUI/
├── docker/                 # ← All Docker files here
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── Makefile
│   ├── start.sh
│   ├── start.bat
│   └── README.md          # ← This file
├── app.py                 # ← Main application
├── requirements.txt       # ← Dependencies
├── sensors/              # ← Sensor modules
├── tabs/                 # ← Dashboard tabs
└── ...                   # ← Other app files
```

### Build Process

1. **Base Image**: Python 3.11 slim (lightweight)
2. **Dependencies**: System packages (gcc, curl)
3. **Security**: Non-root user creation
4. **Python Packages**: Install from requirements.txt
5. **Application**: Copy source code
6. **Configuration**: Environment variables
7. **Health Check**: HTTP endpoint monitoring

## Contributing

### Adding Docker Features

1. **Modify configurations** in this `docker/` folder
2. **Test changes**: `make clean && make dev`
3. **Update documentation**: Keep this README current
4. **Submit PR**: Include Docker testing in description

### Best Practices

- **Keep Docker files in this folder**: Don't scatter them
- **Use Makefile commands**: Consistent for all team members
- **Test both dev and prod modes**: Ensure both work
- **Update docs**: Keep README current with changes

---

## Welcome to Dockerized Development!

You now have a professional, containerized development environment that:
- **Just works** on any machine
- **Stays consistent** across the team
- **Updates easily** with new features
- **Deploys anywhere** when ready

**Happy coding with Cornell Hyperloop!**