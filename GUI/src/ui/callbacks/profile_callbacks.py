"""Profile-related callbacks."""
from dash.dependencies import Input, Output, State
from dash import html
from dash.exceptions import PreventUpdate
import dash

from core.dependencies import container
from services.profile_service import ProfileService, ProfileType
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfileCallbacks:
    """Profile callback manager."""
    
    def __init__(self):
        pass
    
    def register(self, app) -> None:
        """Register profile-related callbacks."""
        self._register_profile_button_callbacks(app)
        self._register_profile_status_callback(app)
    
    def _register_profile_button_callbacks(self, app) -> None:
        """Register profile button callbacks."""
        # Create inputs for all profile buttons
        profile_inputs = [
            Input(f'profile-{profile.command}', 'n_clicks')
            for profile in ProfileType
        ]
        
        @app.callback(
            [Output('profile-output', 'children'),
             Output('current-profile-display', 'children'),
             Output('profile-history-list', 'children')],
            profile_inputs
        )
        def handle_profile_buttons(*button_clicks):
            """Handle profile button clicks."""
            try:
                # Get the triggered context
                ctx = dash.callback_context
                if not ctx.triggered:
                    raise PreventUpdate
                
                # Get the button that was clicked
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                # Extract profile command from button ID
                if not button_id.startswith('profile-'):
                    raise PreventUpdate
                
                command = button_id.replace('profile-', '')
                
                # Get profile service
                profile_service = container.get(ProfileService)
                
                # Find the profile by command
                target_profile = profile_service.get_profile_by_command(command)
                if not target_profile:
                    return "Invalid profile", "None", []
                
                # Check if transition is allowed
                if not profile_service.can_switch_to(target_profile):
                    current = profile_service.get_current_profile()
                    current_name = current.label if current else "None"
                    return (
                        f"Cannot switch to {target_profile.label} from {current_name}",
                        current_name,
                        self._get_history_items(profile_service)
                    )
                
                # Attempt to switch profile
                success = profile_service.switch_profile(target_profile)
                
                if success:
                    return (
                        f"Switched to {target_profile.label}!",
                        target_profile.label,
                        self._get_history_items(profile_service)
                    )
                else:
                    current = profile_service.get_current_profile()
                    current_name = current.label if current else "None"
                    return (
                        f"Failed to switch to {target_profile.label}",
                        current_name,
                        self._get_history_items(profile_service)
                    )
                    
            except Exception as e:
                logger.error(f"Error handling profile button: {e}")
                return f"Error: {e}", "Error", []
    
    def _register_profile_status_callback(self, app) -> None:
        """Register profile status update callback."""
        # Status updates are handled by the button callback above
        pass
    
    def _get_history_items(self, profile_service: ProfileService) -> list:
        """Get profile history items for display."""
        history = profile_service.get_profile_history()
        return [
            html.Li(profile.label) for profile in history[-5:]  # Last 5 profiles
        ]