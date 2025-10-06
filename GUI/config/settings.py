"""Application configuration settings."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CommunicationConfig:
    """Configuration for communication settings."""
    port: str = 'loop://'
    baudrate: int = 115200
    timeout: int = 100
    use_mock: bool = False


@dataclass
class ServerConfig:
    """Configuration for the Dash server."""
    host: str = '127.0.0.1'
    port: int = 8050
    debug: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""
    communication: CommunicationConfig
    server: ServerConfig
    title: str = "Cornell Hyperloop Sensor Dashboard"
    suppress_callback_exceptions: bool = True


def load_config() -> AppConfig:
    """Load configuration from environment variables with sensible defaults."""
    communication_config = CommunicationConfig(
        port=os.environ.get('SERIAL_PORT', 'loop://'),
        baudrate=int(os.environ.get('SERIAL_BAUDRATE', '115200')),
        timeout=int(os.environ.get('SERIAL_TIMEOUT', '100')),
        use_mock=os.environ.get('USE_MOCK_COMMUNICATION', 'false').lower() == 'true'
    )
    
    server_config = ServerConfig(
        host=os.environ.get('DASH_HOST', '127.0.0.1'),
        port=int(os.environ.get('DASH_PORT', '8050')),
        debug=os.environ.get('DASH_DEBUG', 'false').lower() == 'true'
    )
    
    return AppConfig(
        communication=communication_config,
        server=server_config,
        title=os.environ.get('APP_TITLE', "Cornell Hyperloop Sensor Dashboard")
    )