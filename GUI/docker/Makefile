# Makefile for Cornell Hyperloop GUI
.PHONY: help build up down restart logs clean dev prod

# Default target
help:
	@echo "Cornell Hyperloop GUI - Docker Commands"
	@echo "======================================="
	@echo "make build     - Build the Docker image"
	@echo "make up        - Start the application"
	@echo "make down      - Stop the application"
	@echo "make restart   - Restart the application"
	@echo "make logs      - View application logs"
	@echo "make clean     - Remove containers and images"
	@echo "make dev       - Run in development mode"
	@echo "make prod      - Run in production mode"

# Build the Docker image
build:
	@echo "Building Cornell Hyperloop GUI Docker image..."
	docker-compose build

# Start the application
up:
	@echo "Starting Cornell Hyperloop GUI..."
	docker-compose up -d
	@echo "Application is starting... Visit http://localhost:8050"

# Stop the application
down:
	@echo "Stopping Cornell Hyperloop GUI..."
	docker-compose down

# Restart the application
restart: down up

# View logs
logs:
	docker-compose logs -f hyperloop-gui

# Clean up containers and images
clean:
	@echo "Cleaning up Docker containers and images..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Development mode (with volume mounting for live changes)
dev:
	@echo "Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production mode (without volume mounting)
prod:
	@echo "Starting in production mode..."
	docker-compose up -d --build