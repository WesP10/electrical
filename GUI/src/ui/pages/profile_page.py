"""VFD Profile management page."""
from dash import html
import dash_bootstrap_components as dbc

from ui.components.profile import ProfileSelector, ProfileStatus, ProfileHistory
from services.profile_service import ProfileType
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfilePage:
    """VFD Profile management page."""
    
    def __init__(self):
        self.profile_selector = ProfileSelector(list(ProfileType))
        self.profile_status = ProfileStatus()
        self.profile_history = ProfileHistory()
    
    def create_layout(self) -> html.Div:
        """Create the VFD profile page layout."""
        return dbc.Container([
            # Page header
            dbc.Row([
                dbc.Col([
                    html.H2([
                        html.I(className="fas fa-cog me-2"),
                        "VFD Operational Profiles"
                    ], className="text-primary mb-0"),
                    html.P(
                        "Manage and execute Vehicle for the Future operational profiles",
                        className="text-muted mb-3"
                    )
                ])
            ], className="mb-4"),
            
            dbc.Row([
                # Profile selector - takes full width on mobile, 8 cols on desktop
                dbc.Col([
                    self.profile_selector.create()
                ], width=12, lg=8, className="mb-4"),
                
                # Status and history sidebar
                dbc.Col([
                    self.profile_status.create(),
                    html.Hr(className="my-3"),
                    self.profile_history.create()
                ], width=12, lg=4)
            ], className="g-4")
        ], fluid=True, id="profile-page", className="py-3")
