"""Profile management components."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Any

from services.profile_service import ProfileType
from ui.components.common import InfoCard, StatusIndicator
import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfileButton:
    """Profile button component."""
    
    def __init__(self, profile: ProfileType):
        self.profile = profile
    
    def create(self) -> dbc.Button:
        """Create a profile button."""
        return dbc.Button(
            self.profile.label,
            id=f"profile-{self.profile.command}",
            color=self.profile.color,
            className="mb-2",
            style={"width": "100%"}
        )


class ProfileSelector:
    """Profile selector component."""
    
    def __init__(self, profiles: List[ProfileType]):
        self.profiles = profiles
    
    def create_buttons(self) -> List[dbc.Button]:
        """Create profile buttons."""
        buttons = []
        for profile in self.profiles:
            button = ProfileButton(profile).create()
            buttons.append(button)
        return buttons
    
    def create(self) -> html.Div:
        """Create the profile selector component."""
        buttons = self.create_buttons()
        
        return html.Div([
            html.H2("Select Profile", className="text-center mb-4"),
            *buttons,
            html.Div(id="profile-output", className="mt-4 text-center"),
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "80vh",
        })


class ProfileStatus:
    """Profile status display component."""
    
    def __init__(self):
        pass
    
    def create(self, current_profile: str = "None") -> dbc.Card:
        """Create profile status card."""
        return InfoCard.create(
            title="Current Profile",
            content=[
                html.H4(current_profile, id="current-profile-display"),
                StatusIndicator.create("active" if current_profile != "None" else "inactive", "profile-status")
            ],
            card_id="profile-status-card"
        )


class ProfileHistory:
    """Profile history component."""
    
    def create(self, history: List[str] = None) -> dbc.Card:
        """Create profile history card."""
        if not history:
            history = []
        
        history_items = [
            html.Li(profile) for profile in history[-5:]  # Show last 5 profiles
        ]
        
        return InfoCard.create(
            title="Profile History",
            content=[
                html.Ul(history_items, id="profile-history-list") if history_items else 
                html.P("No profile history", className="text-muted")
            ],
            card_id="profile-history-card"
        )