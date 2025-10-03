"""Common UI components."""
from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import List, Dict, Any, Optional

from config.log_config import get_logger

logger = get_logger(__name__)


class NavigationBar:
    """Navigation bar component."""
    
    def __init__(self, title: str = "Cornell Hyperloop Dashboard"):
        self.title = title
    
    def create(self, show_emergency: bool = True) -> dbc.Navbar:
        """Create the navigation bar component."""
        children = [
            dbc.NavbarBrand(self.title, className="ms-2")
        ]
        
        if show_emergency:
            children.append(
                dbc.Button(
                    "Emergency",
                    id="emergency-button",
                    color="danger",
                    className="ms-auto"
                )
            )
        
        return dbc.Navbar(
            dbc.Container(children),
            color="primary",
            dark=True,
            className="mb-4"
        )


class TabContainer:
    """Container for managing tabs."""
    
    def __init__(self):
        self.tabs: List[Dict[str, Any]] = []
    
    def add_tab(self, tab_id: str, label: str, content: Any = None) -> None:
        """Add a tab to the container."""
        self.tabs.append({
            'id': tab_id,
            'label': label,
            'content': content
        })
    
    def create_tabs(self) -> List[dcc.Tab]:
        """Create the tab components."""
        return [
            dcc.Tab(label=tab['label'], value=tab['id'])
            for tab in self.tabs
        ]
    
    def get_default_tab(self) -> Optional[str]:
        """Get the default tab ID."""
        return self.tabs[0]['id'] if self.tabs else None


class LoadingSpinner:
    """Loading spinner component."""
    
    @staticmethod
    def create(component_id: str, children: Any = None) -> dcc.Loading:
        """Create a loading spinner."""
        return dcc.Loading(
            id=f"loading-{component_id}",
            children=children or html.Div(id=component_id),
            type="default"
        )


class ErrorAlert:
    """Error alert component."""
    
    @staticmethod
    def create(message: str, alert_id: str = "error-alert") -> dbc.Alert:
        """Create an error alert."""
        return dbc.Alert(
            message,
            id=alert_id,
            color="danger",
            dismissable=True,
            is_open=True
        )


class InfoCard:
    """Information card component."""
    
    @staticmethod
    def create(title: str, content: Any, card_id: str = None) -> dbc.Card:
        """Create an information card."""
        return dbc.Card([
            dbc.CardHeader(html.H5(title, className="mb-0")),
            dbc.CardBody(content)
        ], id=card_id, className="mb-3")


class StatusIndicator:
    """Status indicator component."""
    
    @staticmethod
    def create(status: str, indicator_id: str = "status-indicator") -> dbc.Badge:
        """Create a status indicator badge."""
        color_map = {
            'connected': 'success',
            'disconnected': 'danger',
            'warning': 'warning',
            'info': 'info',
            'active': 'success',
            'inactive': 'secondary'
        }
        
        return dbc.Badge(
            status.title(),
            id=indicator_id,
            color=color_map.get(status.lower(), 'secondary'),
            className="ms-2"
        )


class CallbackStore:
    """Callback data store component."""
    
    @staticmethod
    def create(store_id: str = "callback-store") -> dcc.Store:
        """Create a callback data store."""
        return dcc.Store(
            id=store_id,
            storage_type='session'
        )


class IntervalComponent:
    """Interval component for periodic updates."""
    
    @staticmethod
    def create(interval_id: str, interval_ms: int = 1000, n_intervals: int = 0) -> dcc.Interval:
        """Create an interval component."""
        return dcc.Interval(
            id=interval_id,
            interval=interval_ms,
            n_intervals=n_intervals
        )