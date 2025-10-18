"""Dependency injection container for the application."""
from typing import Any, Dict, Type, TypeVar, Optional, Callable
import sys
from pathlib import Path
# Use PYTHONPATH for imports
from config.settings import AppConfig
from config.log_config import get_logger

T = TypeVar('T')

logger = get_logger(__name__)


class DependencyContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, interface: Type[T], implementation: Any, singleton: bool = True) -> None:
        """Register a service implementation."""
        key = self._get_key(interface)
        if singleton:
            self._singletons[key] = implementation
        else:
            self._services[key] = implementation
        logger.debug(f"Registered {key} as {'singleton' if singleton else 'transient'}")
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> None:
        """Register a factory function for a service."""
        key = self._get_key(interface)
        self._factories[key] = factory
        if singleton:
            # Create singleton instance immediately
            self._singletons[key] = factory()
        logger.debug(f"Registered factory for {key} as {'singleton' if singleton else 'transient'}")
    
    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        key = self._get_key(interface)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check regular services
        if key in self._services:
            return self._services[key]
        
        # Check factories
        if key in self._factories:
            return self._factories[key]()
        
        raise ValueError(f"Service {key} not registered")
    
    def has(self, interface: Type[T]) -> bool:
        """Check if a service is registered."""
        key = self._get_key(interface)
        return key in self._services or key in self._factories or key in self._singletons
    
    def _get_key(self, interface: Type[T]) -> str:
        """Get the key for a service interface."""
        return f"{interface.__module__}.{interface.__name__}"


# Global container instance
container = DependencyContainer()