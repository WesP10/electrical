"""Main application layout."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Optional, List

from ui.components.common import NavigationBar, TabContainer, CallbackStore
from ui.pages.sensor_page import SensorDashboardPage
from ui.pages.profile_page import ProfilePage
from core.dependencies import container
from services.sensor_service import SensorService
from services.profile_service import ProfileService
from config.log_config import get_logger

logger = get_logger(__name__)


class MainLayout:
    """Main application layout manager."""
    
    def __init__(self):
        self.navbar = NavigationBar()
        self.tab_container = TabContainer()
        self._setup_pages()
    
    def _setup_pages(self) -> None:
        """Setup application pages."""
        try:
            # Get sensor service and create sensor page
            sensor_service = container.get(SensorService)
            sensor_names = sensor_service.get_sensor_names()
            sensor_page = SensorDashboardPage(sensor_names)
            
            # Add tabs
            self.tab_container.add_tab(
                'sensors',
                'Sensors',
                sensor_page.create_layout()
            )
            
            # Add profile page
            profile_page = ProfilePage()
            self.tab_container.add_tab(
                'profiles',
                'Profiles',
                profile_page.create_layout()
            )
            
            logger.info("Pages setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup pages: {e}")
            # Create minimal fallback layout
            self.tab_container.add_tab(
                'error',
                'Error',
                html.Div([
                    html.H3("Application Error"),
                    html.P(f"Failed to initialize application: {e}")
                ])
            )
    
    def create_layout(self) -> html.Div:
        """Create the main application layout."""
        try:
            # Create tabs
            tabs = self.tab_container.create_tabs()
            default_tab = self.tab_container.get_default_tab()
            
            return html.Div([
                # Callback store for session data
                CallbackStore.create(),
                
                # Main card container
                dbc.Card([
                    # Navigation bar
                    self.navbar.create(),
                    
                    # Tab container
                    dbc.Container([
                        dcc.Tabs(
                            id='main-tabs',
                            value=default_tab,
                            children=tabs
                        ),
                        html.Div(id='main-tabs-content')
                    ], fluid=True)
                    
                ], body=True, className="mt-3")
            ])
            
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
            
            # Register main callbacks
            main_callbacks = MainCallbacks(self.tab_container)
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
            Output('main-tabs-content', 'children'),
            [Input('main-tabs', 'value')]
        )
        def render_tab_content(tab_value):
            return html.Div([
                html.H3("Tab Error"),
                html.P(f"Unable to load content for tab: {tab_value}")
            ])