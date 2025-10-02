@echo off
REM Cornell Hyperloop GUI - Quick Start Script for Windows
REM This script automates the entire setup process for new team members

echo Cornell Hyperloop GUI - Automated Setup
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    echo         Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is installed and running

REM Navigate to docker directory (current directory)
cd /d "%~dp0"

echo [INFO] Building Cornell Hyperloop GUI...
docker-compose build

echo [INFO] Starting the application...
docker-compose up -d

echo [INFO] Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check if application is running
powershell -Command "try { Invoke-WebRequest -Uri http://localhost:8050 -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '[OK] Application is running successfully!'; Write-Host '[INFO] Open your browser and visit: http://localhost:8050' } catch { Write-Host '[WARN] Application is starting up. Please wait a moment and visit: http://localhost:8050' }"

echo.
echo Useful commands:
echo    docker-compose logs -f    # View logs
echo    docker-compose down       # Stop the application  
echo    docker-compose restart    # Restart the application
echo.
echo Setup complete! Happy coding!
pause