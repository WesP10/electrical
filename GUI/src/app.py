#!/usr/bin/env python3
"""Main application entry point for the Cornell Hyperloop GUI."""

import os
import sys
import argparse
from typing import Optional

# Set up environment (Docker-friendly, no hardcoded paths)
from config.environment import setup_environment
setup_environment()

from core.application import HyperloopGUIApplication
from config.settings import load_config
from config.log_config import setup_logging, get_logger

logger = get_logger(__name__)


def run_application(debug=True, host="0.0.0.0", port=8050):
    """Run the main application with specified configuration."""
    try:
        # Setup logging first
        setup_logging()
        logger.info("Starting Cornell Hyperloop GUI Application")
        
        # Override environment variables with command line arguments
        os.environ["DASH_DEBUG"] = str(debug).lower()
        os.environ["DASH_HOST"] = host
        os.environ["DASH_PORT"] = str(port)
        
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


def run_tests():
    """Run the test architecture script."""
    try:
        setup_logging()
        logger.info("Running application tests")
        
        import test_architecture
        logger.info("Tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)


def main():
    """Main application entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Cornell Hyperloop GUI")
    parser.add_argument("--debug", action="store_true", default=True, help="Enable debug mode (default: True)")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8050, help="Port to bind to (default: 8050)")
    parser.add_argument("--test", action="store_true", help="Run tests instead of application")
    
    args = parser.parse_args()
    
    # Handle debug flag logic
    debug_mode = args.debug and not args.no_debug
    
    if args.test:
        run_tests()
    else:
        run_application(
            debug=debug_mode,
            host=args.host,
            port=args.port
        )


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
