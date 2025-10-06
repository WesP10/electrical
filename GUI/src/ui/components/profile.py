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
    
    def create_profile_card(self, profile: ProfileType) -> dbc.Card:
        """Create a profile card."""
        return dbc.Card([
            dbc.CardBody([
                html.H5(profile.label, className="card-title text-center mb-3"),
                html.P(f"Command: {profile.command}", className="text-muted text-center small mb-3"),
                dbc.Button(
                    "Select Profile",
                    id=f"profile-{profile.command}",
                    color=profile.color,
                    className="w-100",
                    size="lg"
                )
            ])
        ], className="mb-3 shadow-sm hover-lift", style={"height": "100%"})
    
    def create(self) -> html.Div:
        """Create the profile selector component."""
        # Create profile cards in a grid
        profile_cards = []
        for profile in self.profiles:
            card = self.create_profile_card(profile)
            profile_cards.append(
                dbc.Col(card, width=12, sm=6, lg=4, xl=3, className="mb-3")
            )
        
        return html.Div([
            html.H2("Select Profile", className="mb-4"),
            html.Hr(),
            dbc.Alert(
                id="profile-output",
                is_open=False,
                dismissable=True,
                className="mb-4"
            ),
            dbc.Row(profile_cards, className="g-3")
        ])


class ProfileStatus:
    """Profile status display component."""
    
    def __init__(self):
        pass
    
    def create(self, current_profile: str = "None") -> dbc.Card:
        """Create profile status card."""
        return dbc.Card([
            dbc.CardHeader(
                html.H5("Current Profile", className="mb-0")
            ),
            dbc.CardBody([
                html.Div([
                    html.Span("Active Profile", className="text-muted d-block mb-2"),
                    html.H4(current_profile, id="current-profile-display", className="mb-3 fw-bold text-primary")
                ]),
                html.Div([
                    html.Span("Status: ", className="text-muted"),
                    StatusIndicator.create(
                        "active" if current_profile != "None" else "inactive",
                        "profile-status"
                    )
                ], className="d-flex align-items-center")
            ], className="p-3")
        ], id="profile-status-card", className="mb-3 shadow-sm")


class ProfileHistory:
    """Profile history component."""
    
    def create(self, history: List[str] = None) -> dbc.Card:
        """Create profile history card."""
        if not history:
            history = []
        
        history_items = [
            html.Li(profile, className="mb-1") for profile in history[-5:]  # Show last 5 profiles
        ]
        
        return dbc.Card([
            dbc.CardHeader(
                html.H5("Profile History", className="mb-0")
            ),
            dbc.CardBody([
                html.Ul(
                    history_items if history_items else [html.Li("No profile history", className="text-muted list-unstyled")],
                    id="profile-history-list",
                    className="mb-0" if history_items else "list-unstyled mb-0"
                )
            ], className="p-3")
        ], id="profile-history-card", className="mb-3 shadow-sm")