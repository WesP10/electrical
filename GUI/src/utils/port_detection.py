"""
Port Detection Utilities

Utilities for detecting available serial ports and identifying microcontrollers.
Used by the GUI navigation bar and communication services.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time

# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)

try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    logger.warning("PySerial not available - port detection will be limited")
    PYSERIAL_AVAILABLE = False


class PortInfo:
    """Information about a detected serial port."""
    
    def __init__(self, device: str, description: str, manufacturer: str = None, 
                 vid: int = None, pid: int = None, is_microcontroller: bool = False):
        self.device = device
        self.description = description
        self.manufacturer = manufacturer or "Unknown"
        self.vid = vid
        self.pid = pid
        self.is_microcontroller = is_microcontroller
    
    def __str__(self) -> str:
        return f"{self.device} - {self.description}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'device': self.device,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'vid': self.vid,
            'pid': self.pid,
            'is_microcontroller': self.is_microcontroller
        }


class PortDetector:
    """Utility class for detecting serial ports and microcontrollers."""
    
    # Common microcontroller identifiers
    MICROCONTROLLER_KEYWORDS = [
        'arduino', 'esp32', 'esp8266', 'teensy', 'micro', 'uno', 'nano',
        'leonardo', 'mega', 'pro', 'usb serial', 'ch340', 'ftdi', 'cp210',
        'cp2102', 'cp2104', 'pl2303', 'silicon labs', 'prolific'
    ]
    
    # Common baud rates for microcontrollers
    STANDARD_BAUD_RATES = [
        9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600
    ]
    
    @classmethod
    def get_available_ports(cls) -> List[PortInfo]:
        """Get all available serial ports."""
        if not PYSERIAL_AVAILABLE:
            logger.warning("PySerial not available - returning empty port list")
            return []
        
        try:
            ports = []
            for port in serial.tools.list_ports.comports():
                # Determine if this looks like a microcontroller
                is_microcontroller = cls._is_microcontroller_port(port)
                
                port_info = PortInfo(
                    device=port.device,
                    description=port.description or "Unknown Device",
                    manufacturer=port.manufacturer,
                    vid=port.vid,
                    pid=port.pid,
                    is_microcontroller=is_microcontroller
                )
                ports.append(port_info)
                
                if is_microcontroller:
                    logger.info(f"Detected microcontroller: {port_info}")
                else:
                    logger.debug(f"Detected serial port: {port_info}")
            
            # Sort ports - microcontrollers first, then by device name
            ports.sort(key=lambda p: (not p.is_microcontroller, p.device))
            return ports
            
        except Exception as e:
            logger.error(f"Error detecting serial ports: {e}")
            return []
    
    @classmethod
    def get_microcontroller_ports(cls) -> List[PortInfo]:
        """Get only ports that appear to be microcontrollers."""
        all_ports = cls.get_available_ports()
        return [port for port in all_ports if port.is_microcontroller]
    
    @classmethod
    def _is_microcontroller_port(cls, port) -> bool:
        """Determine if a port appears to be a microcontroller."""
        # Combine description and manufacturer for searching
        search_text = (
            (port.description or "") + " " + 
            (port.manufacturer or "")
        ).lower()
        
        # Check for microcontroller keywords
        return any(keyword in search_text for keyword in cls.MICROCONTROLLER_KEYWORDS)
    
    @classmethod
    def test_port_connection(cls, device: str, baudrate: int = 115200, timeout: float = 2.0) -> bool:
        """Test if a port can be opened successfully."""
        if not PYSERIAL_AVAILABLE:
            return False
        
        try:
            logger.info(f"Testing connection to {device} at {baudrate} baud")
            test_serial = serial.Serial(
                port=device,
                baudrate=baudrate,
                timeout=timeout,
                exclusive=True
            )
            test_serial.close()
            logger.info(f"Successfully tested connection to {device}")
            return True
        except Exception as e:
            logger.debug(f"Failed to connect to {device}: {e}")
            return False
    
    @classmethod
    def get_port_options_for_dropdown(cls) -> List[Dict]:
        """Get port options formatted for Dash dropdown."""
        options = []
        
        microcontroller_ports = cls.get_microcontroller_ports()
        if microcontroller_ports:
            # Add separator
            options.append({'label': '--- Microcontrollers ---', 'value': 'separator', 'disabled': True})
            
            # Add microcontroller ports
            for port in microcontroller_ports:
                options.append({
                    'label': f'{port.device} - {port.description}',
                    'value': port.device
                })
        
        # Add all ports section if there are non-microcontroller ports
        all_ports = cls.get_available_ports()
        other_ports = [port for port in all_ports if not port.is_microcontroller]
        
        if other_ports:
            options.append({'label': '--- All Serial Ports ---', 'value': 'separator2', 'disabled': True})
            for port in other_ports:
                options.append({
                    'label': f'{port.device} - {port.description}',
                    'value': port.device
                })
        
        return options
    
    @classmethod
    def get_baud_rate_options_for_dropdown(cls) -> List[Dict]:
        """Get baud rate options formatted for Dash dropdown."""
        options = []
        for baud_rate in cls.STANDARD_BAUD_RATES:
            # Format with thousands separator for readability
            formatted_rate = f"{baud_rate:,}"
            options.append({
                'label': f'{formatted_rate} baud',
                'value': baud_rate
            })
        
        return options
    
    @classmethod
    def auto_detect_microcontroller(cls) -> Optional[Tuple[str, int]]:
        """Auto-detect the best microcontroller port and suggested baud rate."""
        microcontroller_ports = cls.get_microcontroller_ports()
        
        if not microcontroller_ports:
            logger.info("No microcontroller ports detected")
            return None
        
        # Try each microcontroller port with common baud rates
        for port in microcontroller_ports:
            for baud_rate in [115200, 9600, 57600]:  # Most common rates first
                if cls.test_port_connection(port.device, baud_rate):
                    logger.info(f"Auto-detected microcontroller: {port.device} at {baud_rate} baud")
                    return port.device, baud_rate
        
        # If no connection test succeeded, return first port with default baud
        first_port = microcontroller_ports[0]
        logger.info(f"Using first microcontroller port: {first_port.device} (connection test failed)")
        return first_port.device, 115200
    
    @classmethod
    def refresh_port_list(cls) -> List[PortInfo]:
        """Refresh and return the current list of available ports."""
        logger.info("Refreshing serial port list")
        return cls.get_available_ports()


# Convenience functions for common operations
def get_available_ports() -> List[PortInfo]:
    """Get all available serial ports."""
    return PortDetector.get_available_ports()


def get_microcontroller_ports() -> List[PortInfo]:
    """Get only microcontroller ports."""
    return PortDetector.get_microcontroller_ports()


def get_port_dropdown_options() -> List[Dict]:
    """Get port options for dropdown."""
    return PortDetector.get_port_options_for_dropdown()


def get_baud_rate_dropdown_options() -> List[Dict]:
    """Get baud rate options for dropdown."""
    return PortDetector.get_baud_rate_options_for_dropdown()


def auto_detect_microcontroller() -> Optional[Tuple[str, int]]:
    """Auto-detect microcontroller port and baud rate."""
    return PortDetector.auto_detect_microcontroller()


if __name__ == "__main__":
    # Test the port detection
    print("Testing port detection...")
    
    ports = get_available_ports()
    print(f"Found {len(ports)} total ports:")
    for port in ports:
        print(f"  {port} (MC: {port.is_microcontroller})")
    
    microcontroller_ports = get_microcontroller_ports()
    print(f"\nFound {len(microcontroller_ports)} microcontroller ports:")
    for port in microcontroller_ports:
        print(f"  {port}")
    
    auto_detected = auto_detect_microcontroller()
    if auto_detected:
        print(f"\nAuto-detected: {auto_detected[0]} at {auto_detected[1]} baud")
    else:
        print("\nNo microcontroller auto-detected")
