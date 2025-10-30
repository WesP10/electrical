#!/usr/bin/env python3
"""
Test script for the separated serial communication architecture.
This tests the serial server and TCP client independently.
"""

import time
import subprocess
import sys
from pathlib import Path

def test_serial_server_standalone():
    """Test that the serial server runs independently."""
    print("Testing Serial Server Standalone...")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    server_script = project_root / "src" / "services" / "serial_server.py"
    
    print(f"Starting serial server: {server_script}")
    print("This should start the server and connect to your Arduino.")
    print("You should see serial data being logged in real-time.")
    print("Press Ctrl+C to stop the server.")
    print()
    
    try:
        # Start server with auto-detection
        result = subprocess.run([
            sys.executable,
            str(server_script),
            "--auto-detect",
            "--tcp-port", "9999"
        ], cwd=project_root)
        
        print(f"Server exited with code: {result.returncode}")
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")

def main():
    """Main test function."""
    print("Serial Communication Architecture Test")
    print("=" * 60)
    print()
    print("This will test the separated PySerial architecture where:")
    print("1. Serial server runs in dedicated process")
    print("2. GUI connects via TCP to receive data")
    print("3. Hot reload doesn't affect Arduino communication")
    print()
    
    choice = input("Start standalone serial server test? (y/n): ").lower().strip()
    if choice == 'y':
        test_serial_server_standalone()
    else:
        print("Test cancelled.")

if __name__ == "__main__":
    main()
