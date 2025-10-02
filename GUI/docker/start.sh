#!/bin/bash

# Cornell Hyperloop GUI - Quick Start Script
# This script automates the entire setup process for new team members

set -e

echo "Cornell Hyperloop GUI - Automated Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker Desktop first."
    echo "        Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "[OK] Docker is installed and running"

# Navigate to docker directory (current directory)
cd "$(dirname "$0")"

echo "[INFO] Building Cornell Hyperloop GUI..."
docker-compose build

echo "[INFO] Starting the application..."
docker-compose up -d

echo "[INFO] Waiting for application to start..."
sleep 10

# Check if application is healthy
if curl -f http://localhost:8050 &> /dev/null; then
    echo "[OK] Application is running successfully!"
    echo "[INFO] Open your browser and visit: http://localhost:8050"
else
    echo "[WARN] Application is starting up. Please wait a moment and visit: http://localhost:8050"
fi

echo ""
echo "Useful commands:"
echo "   docker-compose logs -f    # View logs"
echo "   docker-compose down       # Stop the application"
echo "   docker-compose restart    # Restart the application"
echo ""
echo "Setup complete! Happy coding!"