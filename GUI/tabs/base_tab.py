# tabs/base_tab.py
class BaseTab:
    tab_id = None
    tab_label = None

    @staticmethod
    def get_layout(sensors):
        pass

    @staticmethod
    def register_callbacks(app, sensors):
        pass
