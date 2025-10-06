#!/usr/bin/env python3
"""Main application entry point for the Cornell Hyperloop GUI."""

import os
import sys
from pathlib import Path
from typing import Optional

# Add GUI directory to path for config package imports
current_file = Path(__file__).resolve()
src_dir = current_file.parent
gui_dir = src_dir.parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(gui_dir))

# Set up centralized cache directory
from config.environment import setup_environment
setup_environment()

from core.application import HyperloopGUIApplication
from config.settings import load_config
from config.log_config import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    try:
        # Setup logging first
        setup_logging()
        logger.info("Starting Cornell Hyperloop GUI Application")
        
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded: server={config.server.host}:{config.server.port}")
        
        # Create and run application
        app = HyperloopGUIApplication(config)
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise
    finally:
        logger.info("Application shutdown")


def create_app():
    """Create the application instance for WSGI deployment."""
    try:
        setup_logging()
        config = load_config()
        hyperloop_app = HyperloopGUIApplication(config)
        return hyperloop_app.app
    except Exception as e:
        logger.error(f"Failed to create WSGI app: {e}")
        raise


# For WSGI deployment (e.g., with Gunicorn)
# Only create WSGI app when not running as main module
if __name__ != '__main__':
    app = create_app()
    server = app.server

if __name__ == '__main__':
    main()