"""Main application class."""
from dash import Dash
import dash_bootstrap_components as dbc
from typing import List, Optional

from config.settings import AppConfig, load_config
from config.log_config import setup_logging, get_logger
from core.dependencies import container
from core.exceptions import HyperloopGUIError, CommunicationError
from services.tcp_communication_service import CommunicationService
from services.sensor_service import SensorService
# from services.profile_service import ProfileService
from ui.layout import MainLayout

logger = get_logger(__name__)


class HyperloopGUIApplication:
    """Main application class that orchestrates the entire GUI application."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the application with configuration."""
        self.config = config or load_config()
        self._setup_logging()
        self._setup_dependencies()
        self._app: Optional[Dash] = None
        logger.info("Hyperloop GUI Application initialized")
    
    def _setup_logging(self) -> None:
        """Setup application logging."""
        setup_logging()
        logger.info("Logging configured")
    
    def _setup_dependencies(self) -> None:
        """Setup dependency injection container."""
        try:
            # Register configuration
            container.register(AppConfig, self.config)
            
            # Register services
            communication_service = CommunicationService(self.config.communication)
            container.register(CommunicationService, communication_service)
            
            sensor_service = SensorService(communication_service)
            container.register(SensorService, sensor_service)
            
            # Import and register ProfileService for VFD operational modes
            from services.profile_service import ProfileService
            profile_service = ProfileService(communication_service)
            container.register(ProfileService, profile_service)
            
            logger.info("Dependencies configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup dependencies: {e}")
            raise HyperloopGUIError(f"Dependency setup failed: {e}")
    
    def create_app(self) -> Dash:
        """Create and configure the Dash application."""
        if self._app is not None:
            return self._app
        
        try:
            # Include Font Awesome for icons
            external_stylesheets = [
                dbc.themes.BOOTSTRAP,
                "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
            ]
            
            self._app = Dash(
                __name__,
                external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=self.config.suppress_callback_exceptions,
                title=self.config.title,
                assets_folder='assets'
            )
            
            # Setup layout
            main_layout = MainLayout()
            self._app.layout = main_layout.create_layout()
            
            # Register callbacks
            main_layout.register_callbacks(self._app)
            
            logger.info("Dash application created successfully")
            return self._app
            
        except Exception as e:
            logger.error(f"Failed to create Dash application: {e}")
            raise HyperloopGUIError(f"Application creation failed: {e}")
    
    def run(self) -> None:
        """Run the application server."""
        try:
            app = self.create_app()
            server_config = self.config.server
            
            logger.info(f"Starting server on {server_config.host}:{server_config.port}")
            app.run(
                host=server_config.host,
                port=server_config.port,
                debug=server_config.debug
            )
            
        except Exception as e:
            logger.error(f"Failed to run application: {e}")
            raise HyperloopGUIError(f"Application run failed: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the application and cleanup resources."""
        try:
            # Cleanup services
            if container.has(CommunicationService):
                communication_service = container.get(CommunicationService)
                communication_service.close()
            
            if container.has(SensorService):
                sensor_service = container.get(SensorService)
                sensor_service.shutdown()
            
            logger.info("Application shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    @property
    def app(self) -> Dash:
        """Get the Dash application instance."""
        if self._app is None:
            self._app = self.create_app()
        return self._app
    
    @property
    def server(self):
        """Get the Flask server instance for WSGI deployment."""
        return self.app.server
