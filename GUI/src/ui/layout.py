"""Main application layout."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Optional, List, Dict

from ui.components.common import NavigationBar, Sidebar, CallbackStore
from ui.pages.sensor_page import SensorDashboardPage
from ui.pages.profile_page import ProfilePage
from core.dependencies import container
from services.sensor_service import SensorService
from services.profile_service import ProfileService
from sensors.sensor_registry import sensor_registry
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)

# Content area styling to account for sidebar and fixed navbar
CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
    "paddingTop": "56px",  # Account for fixed navbar height
    "padding": "56px 1rem 2rem 1rem",  # Top, right, bottom, left
    "minHeight": "100vh",  # Full viewport height
    "overflowY": "auto",  # Allow vertical scrolling
    "position": "relative"
}


class MainLayout:
    """Main application layout manager."""
    
    def __init__(self):
        self.navbar = NavigationBar()
        self.sidebar = Sidebar()
        self.pages: Dict[str, any] = {}
        self._setup_pages()
    
    def _setup_pages(self) -> None:
        """Setup application pages and navigation."""
        try:
            # Get sensor names from registry instead of sensor service
            sensor_names = sensor_registry.get_all_sensor_names()
            sensor_page = SensorDashboardPage(sensor_names)
            
            # Add sensor page
            self.pages['sensors'] = sensor_page.create_layout()
            self.sidebar.add_nav_item('sensors', 'Sensor Dashboard', 'fas fa-tachometer-alt')
            
            # Add navigation items for future features (will be implemented as overlays or pages later)
            # These are placeholders in the navigation
            self.sidebar.add_nav_item('driving', 'Driving View', 'fas fa-car')
            self.sidebar.add_nav_item('brakes', 'Brake Control', 'fas fa-stop-circle')
            self.sidebar.add_nav_item('emergency', 'Emergency Stop', 'fas fa-exclamation-triangle', is_critical=True)
            self.sidebar.add_nav_item('safety', 'Safety Verification', 'fas fa-shield-alt')

            # Add profile page
            profile_page = ProfilePage()
            self.pages['profiles'] = profile_page.create_layout()
            self.sidebar.add_nav_item('profiles', 'VFD Profiles', 'fas fa-cog')
            
            # Set default page
            self.default_page = 'sensors'
            
            logger.info("Pages setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup pages: {e}")
            # Create minimal fallback layout
            self.pages['error'] = html.Div([
                html.H3("Application Error"),
                html.P(f"Failed to initialize application: {e}")
            ])
            self.default_page = 'error'
    
    def create_layout(self) -> html.Div:
        """Create the main application layout."""
        try:
            return html.Div([
                # Callback store for session data
                CallbackStore.create(),
                
                # Location component for URL routing
                dcc.Location(id='url', refresh=False),
                
                # Navigation bar (fixed at top)
                self.navbar.create(),
                
                # Sidebar navigation
                self.sidebar.create(),
                
                # Main content area
                html.Div(
                    id='page-content',
                    style=CONTENT_STYLE
                )
            ], style={
                "margin": "0",
                "padding": "0",
                "overflowX": "hidden",
                "scrollBehavior": "smooth"
            })
            
        except Exception as e:
            logger.error(f"Failed to create layout: {e}")
            return html.Div([
                html.H1("Application Error"),
                html.P(f"Failed to create application layout: {e}")
            ])
    
    def register_callbacks(self, app) -> None:
        """Register callbacks for the main layout."""
        try:
            from ui.callbacks.main_callbacks import MainCallbacks
            from ui.callbacks.sensor_callbacks import SensorCallbacks
            from ui.callbacks.profile_callbacks import ProfileCallbacks
            
            # Register main callbacks with pages
            main_callbacks = MainCallbacks(self.pages, self.default_page)
            main_callbacks.register(app)
            
            # Register sensor callbacks
            sensor_callbacks = SensorCallbacks()
            sensor_callbacks.register(app)
            
            # Register profile callbacks
            profile_callbacks = ProfileCallbacks()
            profile_callbacks.register(app)
            
            logger.info("Callbacks registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register callbacks: {e}")
            # Register minimal fallback callbacks
            self._register_fallback_callbacks(app)
    
    def _register_fallback_callbacks(self, app) -> None:
        """Register minimal fallback callbacks."""
        from dash.dependencies import Input, Output
        
        @app.callback(
            Output('page-content', 'children'),
            [Input('url', 'pathname')]
        )
        def render_page_content(pathname):
            return html.Div([
                html.H3("Page Error"),
                html.P(f"Unable to load content for page: {pathname}")
            ])