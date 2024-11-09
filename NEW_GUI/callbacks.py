# callbacks.py
from dash.dependencies import Input, Output
from dash import html
from tabs import get_tab_modules

def register_callbacks(app, sensors):
    tab_modules = get_tab_modules()
    tab_module_dict = {module.tab_id: module for module in tab_modules}
    tab_contents = {module.tab_id: module.get_layout(sensors) for module in tab_modules}

    # Callback to render the content of the tabs
    @app.callback(
        Output('tabs-content', 'children'),
        [Input('tabs', 'value')]
    )
    def render_tab_content(tab_value):
        if tab_value in tab_contents:
            return tab_contents[tab_value]
        else:
            return html.Div('Tab not found')

    # Callback for the Emergency button
    @app.callback(
        Output('emergency-button', 'children'),
        [Input('emergency-button', 'n_clicks')]
    )
    def handle_emergency(n_clicks):
        if n_clicks:
            # Placeholder for emergency action
            print("Emergency button clicked!")
            # Implement emergency procedures here
            return "Emergency Activated"
        else:
            return "Emergency"
