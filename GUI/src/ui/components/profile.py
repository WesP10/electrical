"""VFD Profile management components."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Any

from services.profile_service import ProfileType
from ui.components.common import InfoCard, StatusIndicator
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfileButton:
    """VFD Profile button component."""
    
    def __init__(self, profile: ProfileType):
        self.profile = profile
    
    def create(self) -> dbc.Button:
        """Create a VFD profile button."""
        color_map = {
            ProfileType.SENSORS: "primary",
            ProfileType.COMMUNICATION: "info",
            ProfileType.POWER: "warning",
            ProfileType.DIAGNOSTICS: "success",
            ProfileType.EMERGENCY: "danger"
        }
        
        return dbc.Button(
            [
                html.I(className=f"{self.profile.icon} me-2"),
                self.profile.display_name
            ],
            id=f"profile-{self.profile.command}",
            color=color_map.get(self.profile, "secondary"),
            className="mb-2",
            style={"width": "100%"},
            size="lg"
        )


class ProfileSelector:
    """VFD Profile selector component."""
    
    def __init__(self, profiles: List[ProfileType]):
        self.profiles = profiles
    
    def create_profile_card(self, profile: ProfileType) -> dbc.Card:
        """Create a VFD profile card."""
        color_map = {
            ProfileType.SENSORS: "primary",
            ProfileType.COMMUNICATION: "info", 
            ProfileType.POWER: "warning",
            ProfileType.DIAGNOSTICS: "success",
            ProfileType.EMERGENCY: "danger"
        }
        
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"{profile.icon} fa-2x mb-3 text-{color_map.get(profile, 'secondary')}")
                ], className="text-center"),
                html.H5(profile.display_name, className="card-title text-center mb-2"),
                html.P(profile.description, className="text-muted text-center small mb-3"),
                dbc.Button(
                    [
                        html.I(className="fas fa-play me-2"),
                        "Execute Profile"
                    ],
                    id=f"profile-{profile.command}",
                    color=color_map.get(profile, "secondary"),
                    className="w-100",
                    size="lg"
                )
            ])
        ], className="mb-3 shadow-sm hover-lift h-100", 
           style={"transition": "transform 0.2s", "cursor": "pointer"})
    
    def create(self) -> html.Div:
        """Create the VFD profile selector component."""
        # Create profile cards in a grid
        profile_cards = []
        for profile in self.profiles:
            card = self.create_profile_card(profile)
            profile_cards.append(
                dbc.Col(card, width=12, sm=6, lg=6, xl=4, className="mb-3")
            )
        
        return html.Div([
            html.H3([
                html.I(className="fas fa-rocket me-2"),
                "Available VFD Profiles"
            ], className="mb-4 text-primary"),
            dbc.Alert(
                id="profile-output",
                is_open=False,
                dismissable=True,
                className="mb-4"
            ),
            dbc.Row(profile_cards, className="g-3")
        ])


class ProfileStatus:
    """VFD Profile status display component."""
    
    def __init__(self):
        pass
    
    def create(self, current_profile: str = "None") -> dbc.Card:
        """Create VFD profile status card."""
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-info-circle me-2"),
                    "Current Status"
                ], className="mb-0 text-primary")
            ]),
            dbc.CardBody([
                html.Div([
                    html.Span("Active Profile", className="text-muted d-block mb-2"),
                    html.H5(current_profile, id="current-profile-display", 
                           className="mb-3 fw-bold text-primary")
                ]),
                html.Div([
                    html.Span("System Status: ", className="text-muted"),
                    html.Span("Operational", className="badge bg-success"),
                ], className="d-flex align-items-center justify-content-between mb-2"),
                html.Div([
                    html.Span("Last Execution: ", className="text-muted"),
                    html.Span("--", id="last-execution-time", className="small"),
                ], className="d-flex align-items-center justify-content-between")
            ], className="p-3")
        ], id="profile-status-card", className="mb-3 shadow-sm")


class ProfileHistory:
    """VFD Profile history component."""
    
    def create(self, history: List[Dict[str, Any]] = None) -> dbc.Card:
        """Create VFD profile history card."""
        if not history:
            history = []
        
        history_items = []
        for item in history[-5:]:  # Show last 5 profiles
            if isinstance(item, dict):
                timestamp = item.get('timestamp', '')[:19].replace('T', ' ')  # Format datetime
                display_name = item.get('display_name', 'Unknown Profile')
                duration = item.get('duration', 0)
                
                history_items.append(
                    html.Li([
                        html.Div([
                            html.Strong(display_name),
                            html.Span(f" ({duration:.1f}s)", className="text-muted small ms-1")
                        ]),
                        html.Small(timestamp, className="text-muted")
                    ], className="mb-2 pb-2 border-bottom")
                )
            else:
                history_items.append(
                    html.Li(str(item), className="mb-1")
                )
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-history me-2"),
                    "Execution History"
                ], className="mb-0 text-primary")
            ]),
            dbc.CardBody([
                html.Div(
                    history_items if history_items else [
                        html.P("No profile executions yet", className="text-muted mb-0")
                    ],
                    id="profile-history-list",
                    className="mb-0"
                )
            ], className="p-3", style={"max-height": "300px", "overflow-y": "auto"})
        ], id="profile-history-card", className="mb-3 shadow-sm")
