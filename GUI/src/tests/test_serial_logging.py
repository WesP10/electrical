#!/usr/bin/env python3
"""
Test script to demonstrate the serial logging functionality.
This will connect to COM6 and show all the logs from the pySerial reader.
"""

import sys
import os
import time
from pathlib import Path

# Add GUI directory to path for imports
gui_dir = Path(__file__).parent
sys.path.insert(0, str(gui_dir / "src"))

from services.tcp_communication_service import PySerialCommunication
from config.log_config import setup_logging

def main():
    """Test the serial logging functionality."""
    print("🔧 Testing Serial Logging Functionality")
    print("=" * 50)
    
    # Setup logging to show everything
    setup_logging(level="DEBUG")
    
    print("📡 Connecting to COM6 (Arduino Uno)...")
    
    # Create serial communication with COM6
    comm = PySerialCommunication(
        port="COM6",
        baudrate=9600,  # Standard Arduino baud rate
        timeout=1.0,
        buffer_size=50
    )
    
    # Set up a simple data callback to show what we're receiving
    def data_callback(sensor_name, data_values):
        print(f"📊 Data received for {sensor_name}: {data_values}")
    
    def discovery_callback(sensor_name, pins, payload):
        print(f"🔍 New sensor discovered: {sensor_name} on pins {pins} with payload: {payload}")
        # Register callback for this sensor
        comm.register_data_callback(sensor_name, lambda data: data_callback(sensor_name, data))
    
    comm.set_discovery_callback(discovery_callback)
    
    print("🚀 Starting serial communication...")
    comm.start()
    
    print("📋 Listening for serial data...")
    print("   - Every line received will be logged with 'Serial line received:' prefix")
    print("   - Raw bytes will be logged with 'Raw bytes received:' prefix")
    print("   - Status updates every 30 seconds")
    print("   - Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Keep running and show periodic buffer status
        start_time = time.time()
        last_buffer_check = time.time()
        
        while True:
            time.sleep(1)
            
            # Show buffer status every 10 seconds
            if time.time() - last_buffer_check > 10:
                buffer_lines = comm.get_buffer_lines(5)  # Get last 5 lines
                if buffer_lines:
                    print(f"\n📦 Last 5 buffer lines:")
                    for i, line in enumerate(buffer_lines, 1):
                        print(f"   {i}. '{line}'")
                else:
                    print(f"\n📦 Buffer is empty")
                
                discovered = comm.get_discovered_sensors()
                if discovered:
                    print(f"🔍 Discovered sensors: {discovered}")
                else:
                    print(f"🔍 No sensors discovered yet")
                
                print("-" * 30)
                last_buffer_check = time.time()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping serial communication...")
        comm.close()
        print("✅ Serial communication stopped")

if __name__ == "__main__":
    main()
