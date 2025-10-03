"""Communication service for handling sensor communication."""
from typing import Optional, Dict, Callable, Any
from abc import ABC, abstractmethod

from config.settings import CommunicationConfig
from config.log_config import get_logger
from core.exceptions import CommunicationError

logger = get_logger(__name__)


class BaseCommunication(ABC):
    """Abstract base class for communication implementations."""
    
    @abstractmethod
    def send_command(self, command: str) -> bool:
        """Send a command to the communication channel."""
        pass
    
    @abstractmethod
    def register_callback(self, sensor_id: str, callback: Callable) -> None:
        """Register a callback for sensor data."""
        pass
    
    @abstractmethod
    def deregister_callback(self, sensor_id: str) -> None:
        """Deregister a callback for sensor data."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the communication channel."""
        pass


class CommunicationService:
    """Service for managing communication with sensors and Arduino."""
    
    def __init__(self, config: CommunicationConfig):
        self.config = config
        self._communication: Optional[BaseCommunication] = None
        self._callbacks: Dict[str, Callable] = {}
        self._initialize_communication()
        logger.info(f"Communication service initialized with config: {config}")
    
    def _initialize_communication(self) -> None:
        """Initialize the communication implementation."""
        try:
            if self.config.use_mock:
                self._communication = self._create_mock_communication()
            else:
                self._communication = self._create_serial_communication()
            logger.info("Communication initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize primary communication: {e}")
            logger.info("Falling back to mock communication")
            self._communication = self._create_mock_communication()
    
    def _create_serial_communication(self) -> BaseCommunication:
        """Create a serial communication instance."""
        try:
            from sensors.communication import PySerialCommunication
            return PySerialCommunication(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.timeout
            )
        except ImportError as e:
            raise CommunicationError(f"Serial communication not available: {e}")
        except Exception as e:
            raise CommunicationError(f"Failed to create serial communication: {e}")
    
    def _create_mock_communication(self) -> BaseCommunication:
        """Create a mock communication instance."""
        try:
            from sensors.mock_communication import MockCommunication
            return MockCommunication()
        except ImportError as e:
            raise CommunicationError(f"Mock communication not available: {e}")
        except Exception as e:
            raise CommunicationError(f"Failed to create mock communication: {e}")
    
    def send_command(self, command: str) -> bool:
        """Send a command through the communication channel."""
        if not self._communication:
            logger.error("Communication not initialized")
            return False
        
        try:
            result = self._communication.send_command(command)
            logger.debug(f"Command '{command}' sent with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            return False
    
    def register_callback(self, sensor_id: str, callback: Callable) -> None:
        """Register a callback for sensor data."""
        if not self._communication:
            logger.error("Communication not initialized")
            return
        
        try:
            self._communication.register_callback(sensor_id, callback)
            self._callbacks[sensor_id] = callback
            logger.debug(f"Callback registered for sensor {sensor_id}")
        except Exception as e:
            logger.error(f"Failed to register callback for sensor {sensor_id}: {e}")
    
    def deregister_callback(self, sensor_id: str) -> None:
        """Deregister a callback for sensor data."""
        if not self._communication:
            logger.error("Communication not initialized")
            return
        
        try:
            self._communication.deregister_callback(sensor_id)
            if sensor_id in self._callbacks:
                del self._callbacks[sensor_id]
            logger.debug(f"Callback deregistered for sensor {sensor_id}")
        except Exception as e:
            logger.error(f"Failed to deregister callback for sensor {sensor_id}: {e}")
    
    def is_connected(self) -> bool:
        """Check if communication is available."""
        return self._communication is not None
    
    def get_communication_type(self) -> str:
        """Get the type of communication being used."""
        if not self._communication:
            return "None"
        return type(self._communication).__name__
    
    def close(self) -> None:
        """Close the communication channel."""
        if self._communication:
            try:
                self._communication.close()
                logger.info("Communication closed")
            except Exception as e:
                logger.error(f"Error closing communication: {e}")
            finally:
                self._communication = None
                self._callbacks.clear()