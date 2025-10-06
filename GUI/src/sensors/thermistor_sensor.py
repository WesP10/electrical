from .base_sensor import BaseSensor
from services.communication_service import CommunicationService
from typing import List, Dict

class Sensor(BaseSensor):
    def __init__(self, communication_service: CommunicationService):
        super().__init__(communication_service)
    
    def get_name(self) -> str:
        return 'Thermistor'
    
    def get_sensor_id(self) -> str:
        return 'THERMISTOR_SENSOR'
    
    def get_data_fields(self) -> List[str]:
        return ['temperature']
    
    def get_units(self) -> Dict[str, str]:
        return {'temperature': '°C'}