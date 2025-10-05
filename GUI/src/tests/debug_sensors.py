#!/usr/bin/env python3
"""Debug script to test sensor data flow."""

import sys
import time
from pathlib import Path

# Add GUI directory to path
gui_dir = Path(__file__).parent
src_dir = gui_dir / "src"
sys.path.insert(0, str(src_dir))

from services.communication_service import CommunicationService
from services.sensor_service import SensorService
from config.settings import load_config

def test_sensor_data():
    """Test sensor data generation and retrieval."""
    print("🔍 Testing sensor data flow...")
    
    # Load config
    config = load_config()
    config.communication.use_mock = True
    
    # Initialize services
    comm_service = CommunicationService(config.communication)
    sensor_service = SensorService(comm_service)
    
    print(f"📡 Communication service initialized")
    print(f"🔧 Sensor service initialized")
    
    # Wait for discovery
    print("⏳ Waiting for sensor discovery...")
    for i in range(5):
        time.sleep(1)
        sensor_names = sensor_service.get_sensor_names()
        discovered = comm_service.get_discovered_sensors()
        print(f"   {i+1}s: SensorService={sensor_names}, CommService={discovered}")
    
    # Check discovered sensors
    sensor_names = sensor_service.get_sensor_names()
    print(f"🔍 Final discovered sensors: {sensor_names}")
    
    # Check availability
    for name in sensor_names:
        is_available = sensor_service.is_sensor_available(name)
        print(f"📊 {name}: {'✅ Available' if is_available else '❌ Unavailable'}")
    
    # Wait for data collection
    print("⏳ Waiting for data collection...")
    time.sleep(3)
    
    # Get sensor data
    all_data = sensor_service.get_all_sensor_data()
    print(f"📈 Retrieved data for {len(all_data)} sensors")
    
    for sensor_name, data in all_data.items():
        if data is not None and not data.empty:
            print(f"  📊 {sensor_name}: {len(data)} rows, columns: {list(data.columns)}")
            print(f"    Last few rows:")
            print(data.tail(3).to_string(index=False))
        else:
            print(f"  ❌ {sensor_name}: No data")
    
    # Cleanup
    comm_service.close()
    sensor_service.shutdown()
    print("✅ Test completed")

if __name__ == "__main__":
    test_sensor_data()