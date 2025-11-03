"""Custom exceptions for the application."""


class HyperloopGUIError(Exception):
    """Base exception for Hyperloop GUI application."""
    pass


class CommunicationError(HyperloopGUIError):
    """Exception raised for communication-related errors."""
    pass


class SensorError(HyperloopGUIError):
    """Exception raised for sensor-related errors."""
    pass


class ConfigurationError(HyperloopGUIError):
    """Exception raised for configuration-related errors."""
    pass


class UIError(HyperloopGUIError):
    """Exception raised for UI-related errors."""
    pass
