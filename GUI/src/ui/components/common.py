"""Common UI components."""
from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
# Add GUI directory to path for config package imports
gui_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(gui_dir))
from config.log_config import get_logger

logger = get_logger(__name__)


class NavigationBar:
    """Navigation bar component."""
    
    def __init__(self, title: str = "Cornell Hyperloop Dashboard"):
        self.title = title
    
    def create(self, show_status: bool = True) -> dbc.Navbar:
        """Create the navigation bar component."""
        children = [
            dbc.NavbarBrand(self.title, className="ms-2")
        ]
        
        if show_status:
            children.append(
                html.Div(
                    [
                        html.Span("System Status: ", className="me-2 text-light"),
                        dbc.Badge("Active", id="system-status-badge", color="success")
                    ],
                    className="ms-auto d-flex align-items-center"
                )
            )
        
        return dbc.Navbar(
            dbc.Container(children, fluid=True),
            color="primary",
            dark=True,
            sticky="top",
            className="mb-0",
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "right": 0,
                "zIndex": 1030
            }
        )


class Sidebar:
    """Sidebar navigation component."""
    
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": "76px",  # Below fixed navbar (56px + padding)
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "backgroundColor": "#f8f9fa",
        "overflowY": "auto",
        "zIndex": 1020
    }
    
    def __init__(self):
        self.nav_items = []
    
    def add_nav_item(self, item_id: str, label: str, icon: str = None, is_critical: bool = False) -> None:
        """Add a navigation item to the sidebar."""
        self.nav_items.append({
            'id': item_id,
            'label': label,
            'icon': icon,
            'is_critical': is_critical
        })
    
    def create(self) -> html.Div:
        """Create the sidebar component."""
        nav_links = []
        
        for item in self.nav_items:
            # Create link content
            link_content = []
            if item['icon']:
                link_content.append(html.I(className=f"{item['icon']} me-2"))
            link_content.append(item['label'])
            
            # Determine styling based on criticality
            if item['is_critical']:
                className = "nav-link text-danger fw-bold"
            else:
                className = "nav-link text-dark"
            
            nav_links.append(
                dbc.NavLink(
                    link_content,
                    href=f"/{item['id']}",
                    id=f"nav-{item['id']}",
                    className=className
                )
            )
        
        return html.Div(
            [
                html.H4("Navigation", className="mb-3"),
                html.Hr(),
                dbc.Nav(nav_links, vertical=True, pills=True)
            ],
            style=self.SIDEBAR_STYLE,
            id="sidebar"
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