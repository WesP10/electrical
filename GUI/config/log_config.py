"""Logging configuration for the application."""
import logging
import sys
import os
from typing import Optional


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """Setup application logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    """
    # Check if detailed logging is enabled via environment variable
    enable_detailed_logs = os.environ.get("ENABLE_DETAILED_LOGS", "false").lower() == "true"
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # If detailed logging is disabled, set most loggers to WARNING or higher
    if not enable_detailed_logs:
        # Only show WARNING and ERROR messages by default
        log_level = logging.WARNING
    else:
        # Show all INFO and above when detailed logging is enabled
        log_level = getattr(logging, level.upper())
    
    logging.basicConfig(
        level=log_level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('dash').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Application-specific loggers
    if not enable_detailed_logs:
        # Suppress INFO logs from application modules when detailed logging is off
        logging.getLogger('services').setLevel(logging.WARNING)
        logging.getLogger('ui.callbacks').setLevel(logging.WARNING)
        logging.getLogger('core').setLevel(logging.WARNING)
        logging.getLogger('sensors').setLevel(logging.WARNING)
        logging.getLogger('utils').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)