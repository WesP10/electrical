from .base_sensor import BaseSensor
from services.communication_service import CommunicationService
from typing import List, Dict

class Sensor(BaseSensor):
    def __init__(self, communication_service: CommunicationService):
        super().__init__(communication_service)
    
    def get_name(self) -> str:
        return 'Relay Control'
    
    def get_sensor_id(self) -> str:
        return 'RELAY_SENSOR'
    
    def get_data_fields(self) -> List[str]:
        return ['state', 'voltage']
    
    def get_units(self) -> Dict[str, str]:
        return {'state': 'bool', 'voltage': 'V'}