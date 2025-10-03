"""Main application callbacks."""
from dash.dependencies import Input, Output
from dash import html
from typing import Dict, Any

from ui.components.common import TabContainer
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class MainCallbacks:
    """Main application callback manager."""
    
    def __init__(self, tab_container: TabContainer):
        self.tab_container = tab_container
    
    def register(self, app) -> None:
        """Register main application callbacks."""
        self._register_tab_callback(app)
        self._register_emergency_callback(app)
    
    def _register_tab_callback(self, app) -> None:
        """Register tab switching callback."""
        @app.callback(
            Output('main-tabs-content', 'children'),
            [Input('main-tabs', 'value')]
        )
        def render_tab_content(tab_value):
            """Render content for the selected tab."""
            try:
                for tab in self.tab_container.tabs:
                    if tab['id'] == tab_value:
                        return tab['content']
                
                return html.Div([
                    html.H3("Tab Not Found"),
                    html.P(f"Tab '{tab_value}' could not be loaded.")
                ])
                
            except Exception as e:
                logger.error(f"Error rendering tab content: {e}")
                return html.Div([
                    html.H3("Error"),
                    html.P(f"Failed to render tab content: {e}")
                ])
    
    def _register_emergency_callback(self, app) -> None:
        """Register emergency button callback."""
        @app.callback(
            Output('emergency-button', 'children'),
            [Input('emergency-button', 'n_clicks')]
        )
        def handle_emergency(n_clicks):
            """Handle emergency button clicks."""
            if n_clicks:
                try:
                    # Get profile service and trigger emergency
                    from core.dependencies import container
                    from services.profile_service import ProfileService
                    
                    profile_service = container.get(ProfileService)
                    success = profile_service.emergency_stop()
                    
                    if success:
                        logger.warning("Emergency stop activated")
                        return "Emergency Activated"
                    else:
                        logger.error("Emergency stop failed")
                        return "Emergency Failed"
                        
                except Exception as e:
                    logger.error(f"Emergency button error: {e}")
                    return "Emergency Error"
            
            return "Emergency"