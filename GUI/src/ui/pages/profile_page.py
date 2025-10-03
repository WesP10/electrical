"""Profile management page."""
from dash import html
import dash_bootstrap_components as dbc

from ui.components.profile import ProfileSelector, ProfileStatus, ProfileHistory
from services.profile_service import ProfileType
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfilePage:
    """Profile management page."""
    
    def __init__(self):
        self.profile_selector = ProfileSelector(list(ProfileType))
        self.profile_status = ProfileStatus()
        self.profile_history = ProfileHistory()
    
    def create_layout(self) -> html.Div:
        """Create the profile page layout."""
        return dbc.Container([
            dbc.Row([
                # Profile selector
                dbc.Col([
                    self.profile_selector.create()
                ], width=12, md=8),
                
                # Status and history
                dbc.Col([
                    self.profile_status.create(),
                    html.Div(className="mb-3"),  # Spacer
                    self.profile_history.create()
                ], width=12, md=4)
            ])
        ], fluid=True, id="profile-page")