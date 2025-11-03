from .base_sensor import BaseSensor
from services.tcp_communication_service import CommunicationService
from typing import List, Dict

class Sensor(BaseSensor):
    def __init__(self, communication_service: CommunicationService):
        super().__init__(communication_service)
    
    def get_name(self) -> str:
        return 'nRF24L01 Radio'
    
    def get_sensor_id(self) -> str:
        return 'NRF24L01_SENSOR'
    
    def get_data_fields(self) -> List[str]:
        return ['signal_strength', 'data_rate', 'packet_count']
    
    def get_units(self) -> Dict[str, str]:
        return {'signal_strength': 'dBm', 'data_rate': 'kbps', 'packet_count': 'count'}
