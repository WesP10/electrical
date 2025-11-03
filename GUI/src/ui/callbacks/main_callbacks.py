"""Main application callbacks."""
from dash.dependencies import Input, Output, State
from dash import html
from typing import Dict, Any

from config.log_config import get_logger

logger = get_logger(__name__)


class MainCallbacks:
    """Main application callback manager."""
    
    def __init__(self, pages: Dict[str, Any], default_page: str = 'sensors'):
        self.pages = pages
        self.default_page = default_page
    
    def register(self, app) -> None:
        """Register main application callbacks."""
        self._register_navigation_callback(app)
        self._register_active_link_callback(app)
        self._register_emergency_callback(app)
    
    def _register_navigation_callback(self, app) -> None:
        """Register sidebar navigation callback."""
        @app.callback(
            Output('page-content', 'children'),
            [Input('url', 'pathname')]
        )
        def display_page(pathname):
            """Display the appropriate page based on URL pathname."""
            try:
                # Parse pathname to get page ID
                if pathname is None or pathname == '/':
                    page_id = self.default_page
                else:
                    # Remove leading slash and get page ID
                    page_id = pathname.strip('/').split('/')[0]
                
                # Check if page exists
                if page_id in self.pages:
                    return self.pages[page_id]
                
                # For future pages not yet implemented, show placeholder
                future_pages = {
                    'driving': 'Driving View',
                    'brakes': 'Brake Control',
                    'emergency': 'Emergency Stop',
                    'safety': 'Safety Verification'
                }
                
                if page_id in future_pages:
                    return html.Div([
                        html.H2(future_pages[page_id], className="mb-4"),
                        html.Hr(),
                        html.P([
                            "This feature is under development and will be available soon. ",
                            "It may be implemented as a full page or an overlay depending on use case requirements."
                        ], className="text-muted")
                    ])
                
                # Default 404 page
                return html.Div([
                    html.H2("404: Page Not Found", className="mb-4"),
                    html.P(f"The page '{page_id}' does not exist."),
                    html.A("Return to Dashboard", href="/sensors", className="btn btn-primary")
                ])
                
            except Exception as e:
                logger.error(f"Error displaying page: {e}")
                return html.Div([
                    html.H3("Error"),
                    html.P(f"Failed to render page content: {e}")
                ])
    
    def _register_active_link_callback(self, app) -> None:
        """Register callback to highlight active navigation link."""
        nav_items = ['sensors', 'driving', 'brakes', 'emergency', 'safety', 'profiles']
        
        @app.callback(
            [Output(f'nav-{item}', 'active') for item in nav_items],
            [Input('url', 'pathname')]
        )
        def update_active_links(pathname):
            """Update which navigation link is active based on current page."""
            try:
                if pathname is None or pathname == '/':
                    current_page = self.default_page
                else:
                    current_page = pathname.strip('/').split('/')[0]
                
                # Return True for the active page, False for all others
                return [item == current_page for item in nav_items]
                
            except Exception as e:
                logger.error(f"Error updating active links: {e}")
                # Default to sensors page active
                return [item == 'sensors' for item in nav_items]
    
    def _register_emergency_callback(self, app) -> None:
        """Register emergency stop callback for navigation item."""
        @app.callback(
            Output('system-status-badge', 'children'),
            Output('system-status-badge', 'color'),
            [Input('nav-emergency', 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_emergency(n_clicks):
            """Handle emergency stop navigation clicks."""
            if n_clicks:
                try:
                    # Get profile service and trigger emergency (temporarily disabled)
                    # from core.dependencies import container
                    # from services.profile_service import ProfileService
                    
                    # profile_service = container.get(ProfileService)
                    # success = profile_service.emergency_stop()
                    
                    # if success:
                    logger.warning("Emergency stop activated via navigation (profile service disabled)")
                    return "Emergency Active", "danger"
                    # else:
                    #     logger.error("Emergency stop failed")
                    #     return "Emergency Failed", "warning"
                        
                except Exception as e:
                    logger.error(f"Emergency stop error: {e}")
                    return "System Error", "danger"
            
            return "Active", "success"
