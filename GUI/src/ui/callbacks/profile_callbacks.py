"""VFD Profile-related callbacks."""
from dash.dependencies import Input, Output, State
from dash import html, callback_context
from dash.exceptions import PreventUpdate
import dash
import dash_bootstrap_components as dbc
from datetime import datetime

from core.dependencies import container
from services.profile_service import ProfileService, ProfileType
from config.log_config import get_logger

logger = get_logger(__name__)


class ProfileCallbacks:
    """VFD Profile callback manager."""
    
    def __init__(self):
        pass
    
    def register(self, app) -> None:
        """Register VFD profile-related callbacks."""
        self._register_profile_button_callbacks(app)
        self._register_profile_status_callback(app)
    
    def _register_profile_button_callbacks(self, app) -> None:
        """Register VFD profile button callbacks."""
        @app.callback(
            [
                Output('profile-output', 'children'),
                Output('profile-output', 'is_open'),
                Output('profile-output', 'color'),
                Output('current-profile-display', 'children'),
                Output('last-execution-time', 'children'),
                Output('profile-history-list', 'children')
            ],
            [
                Input('profile-sensors', 'n_clicks'),
                Input('profile-communication', 'n_clicks'),
                Input('profile-power', 'n_clicks'),
                Input('profile-diagnostics', 'n_clicks'),
                Input('profile-emergency', 'n_clicks')
            ],
            prevent_initial_call=True
        )
        def handle_profile_execution(sensors_clicks, comm_clicks, power_clicks,
                                   diag_clicks, emergency_clicks):
            """Handle VFD profile execution."""
            try:
                if not callback_context.triggered:
                    raise PreventUpdate
                
                trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
                logger.info(f"VFD Profile execution triggered: {trigger_id}")
                
                # Map button IDs to profile types
                profile_map = {
                    'profile-sensors': ProfileType.SENSORS,
                    'profile-communication': ProfileType.COMMUNICATION,
                    'profile-power': ProfileType.POWER,
                    'profile-diagnostics': ProfileType.DIAGNOSTICS,
                    'profile-emergency': ProfileType.EMERGENCY
                }
                
                if trigger_id not in profile_map:
                    logger.warning(f"Unknown VFD profile trigger: {trigger_id}")
                    return "Unknown profile selected", True, "warning", "None", "--", []
                
                selected_profile = profile_map[trigger_id]
                
                # Get profile service
                profile_service = container.get(ProfileService)
                
                # Execute the profile
                logger.info(f"Executing VFD profile: {selected_profile.display_name}")
                result = profile_service.execute_profile(selected_profile)
                
                # Update timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Get updated history
                history_items = self._get_history_items(profile_service)
                
                if result.get('success', False):
                    message = [
                        html.Div([
                            html.I(className="fas fa-check-circle me-2"),
                            html.Strong("VFD Profile executed successfully!")
                        ]),
                        html.P(f"Profile: {selected_profile.display_name}", className="mb-1"),
                        html.P(result.get('message', 'Profile completed'), className="mb-0 small")
                    ]
                    return message, True, "success", selected_profile.display_name, current_time, history_items
                else:
                    error_msg = result.get('error', 'Unknown error occurred')
                    message = [
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Strong("VFD Profile execution failed!")
                        ]),
                        html.P(f"Profile: {selected_profile.display_name}", className="mb-1"),
                        html.P(f"Error: {error_msg}", className="mb-0 small text-danger")
                    ]
                    return message, True, "danger", "Error", current_time, history_items
                    
            except Exception as e:
                logger.error(f"Error in VFD profile execution: {str(e)}")
                error_message = [
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("System Error!")
                    ]),
                    html.P(f"Failed to execute VFD profile: {str(e)}", className="mb-0 small")
                ]
                return error_message, True, "danger", "Error", "--", []
    
    def _register_profile_status_callback(self, app) -> None:
        """Register VFD profile status update callback."""
        @app.callback(
            Output('profile-status-card', 'children'),
            [Input('current-profile-display', 'children')],
            prevent_initial_call=True
        )
        def update_profile_status_card(current_profile):
            """Update the VFD profile status card."""
            try:
                profile_service = container.get(ProfileService)
                status = profile_service.get_current_status()
                
                return [
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-info-circle me-2"),
                            "VFD System Status"
                        ], className="mb-0 text-primary")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Span("Active Profile", className="text-muted d-block mb-2"),
                            html.H5(current_profile or "None", className="mb-3 fw-bold text-primary")
                        ]),
                        html.Div([
                            html.Span("System Status: ", className="text-muted"),
                            html.Span(
                                status.get('system_status', 'Unknown'),
                                className=f"badge bg-{'success' if status.get('system_status') == 'Operational' else 'warning'}"
                            ),
                        ], className="d-flex align-items-center justify-content-between mb-2"),
                        html.Div([
                            html.Span("VFD Mode: ", className="text-muted"),
                            html.Span(
                                status.get('vfd_mode', 'Standby'),
                                className="badge bg-info"
                            ),
                        ], className="d-flex align-items-center justify-content-between mb-2"),
                        html.Div([
                            html.Span("Last Execution: ", className="text-muted"),
                            html.Span(
                                status.get('last_execution', '--'),
                                className="small"
                            ),
                        ], className="d-flex align-items-center justify-content-between")
                    ], className="p-3")
                ]
                
            except Exception as e:
                logger.error(f"Error updating VFD profile status: {str(e)}")
                return [
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Status Error"
                        ], className="mb-0 text-danger")
                    ]),
                    dbc.CardBody([
                        html.P(f"Error loading VFD status: {str(e)}", className="text-danger mb-0")
                    ], className="p-3")
                ]
    
    def _get_history_items(self, profile_service: ProfileService) -> list:
        """Get VFD profile history items for display."""
        try:
            history = profile_service.get_profile_history()
            history_items = []
            
            for item in history[-5:]:  # Show last 5
                if isinstance(item, dict):
                    timestamp = item.get('timestamp', '')[:19].replace('T', ' ')
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
                    # Fallback for simple string items
                    if hasattr(item, 'display_name'):
                        display_name = item.display_name
                    else:
                        display_name = str(item)
                    
                    history_items.append(
                        html.Li([
                            html.Strong(display_name),
                            html.Small("Legacy entry", className="text-muted ms-2")
                        ], className="mb-1")
                    )
            
            if not history_items:
                history_items = [html.P("No VFD profile executions yet", className="text-muted mb-0")]
            
            return history_items
            
        except Exception as e:
            logger.error(f"Error getting VFD profile history: {str(e)}")
            return [html.P("Error loading history", className="text-danger mb-0")]
