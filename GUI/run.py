#!/usr/bin/env python3
"""
Cornell Hyperloop GUI - Intelligent Launcher
Usage: python run.py

This launcher automatically detects:
- Operating System (Windows/Linux/MacOS)
- Microcontroller connection status
- Automatically starts serial communication server for Arduino
- Optimal launcher script to use
- Cache directory setup

New team members only need to run: python run.py
"""
import os
import sys
import platform
import subprocess
import time
import signal
import atexit
from pathlib import Path
import serial.tools.list_ports

# Global variable to track serial server process
serial_server_process = None

def cleanup_serial_server():
    """Clean up the serial server process on exit."""
    global serial_server_process
    if serial_server_process:
        print("[CLEANUP] Stopping serial communication server...")
        try:
            serial_server_process.terminate()
            # Give it a few seconds to terminate gracefully
            try:
                serial_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[CLEANUP] Force killing serial server...")
                serial_server_process.kill()
                serial_server_process.wait()
        except Exception as e:
            print(f"[WARNING] Error stopping serial server: {e}")
        serial_server_process = None

def start_serial_server(microcontroller_port, baudrate=115200):
    """Start the dedicated serial communication server."""
    global serial_server_process
    
    # Check if server is already running on port 9999
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = test_socket.connect_ex(('localhost', 9999))
        test_socket.close()
        if result == 0:
            print("[INFO] Serial server already running on port 9999")
            return True
    except:
        pass
    
    try:
        print(f"[SERVER] Starting serial communication server for {microcontroller_port}...")
        
        # Path to the serial server script
        project_root = Path(__file__).parent
        server_script = project_root / "src" / "services" / "serial_server.py"
        
        if not server_script.exists():
            print(f"[ERROR] Serial server script not found: {server_script}")
            return False
        
        # Use virtual environment Python if available
        venv_python = project_root.parent / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_executable = str(venv_python)
        else:
            python_executable = sys.executable
        
        # Start the server process
        cmd = [
            python_executable,
            str(server_script),
            "--port", microcontroller_port,
            "--baudrate", str(baudrate),
            "--tcp-port", "9999"
        ]
        
        print(f"[SERVER] Command: {' '.join(cmd)}")
        serial_server_process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Check if the server started successfully
        if serial_server_process.poll() is None:
            print(f"[SERVER] Serial communication server started (PID: {serial_server_process.pid})")
            
            # Register cleanup function
            atexit.register(cleanup_serial_server)
            
            return True
        else:
            print("[ERROR] Serial server failed to start")
            # Try to get error output
            try:
                output, _ = serial_server_process.communicate(timeout=1)
                print(f"[ERROR] Server output: {output}")
            except:
                pass
            serial_server_process = None
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to start serial server: {e}")
        return False

def detect_microcontroller():
    """Detect if a microcontroller is connected via serial ports."""
    try:
        ports = serial.tools.list_ports.comports()
        microcontroller_keywords = [
            'arduino', 'esp32', 'esp8266', 'teensy', 'micro', 'uno', 'nano',
            'leonardo', 'mega', 'pro', 'USB Serial', 'CH340', 'FTDI', 'CP210'
        ]
        
        for port in ports:
            port_info = (port.description + " " + (port.manufacturer or "")).lower()
            if any(keyword.lower() in port_info for keyword in microcontroller_keywords):
                print(f"[OK] Microcontroller detected: {port.device} - {port.description}")
                return True, port.device
        
        print("[WARNING] No microcontroller detected - using mock communication")
        return False, None
    except Exception as e:
        print(f"[WARNING] Could not scan for microcontrollers: {e}")
        print("   Using mock communication as fallback")
        return False, None

def setup_cache_directory():
    """Set up centralized cache directory."""
    project_root = Path(__file__).parent
    cache_dir = project_root / "__pycache__"
    
    # Create cache directory if it doesn't exist
    cache_dir.mkdir(exist_ok=True)
    
    # Set environment variable for this session
    os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir)
    
    return cache_dir

def get_optimal_launcher():
    """Determine the best launcher script based on OS and availability."""
    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    
    system = platform.system().lower()
    
    if system == "windows":
        # Prefer PowerShell, fallback to batch
        ps_launcher = config_dir / "run.ps1"
        bat_launcher = config_dir / "run.bat"
        
        if ps_launcher.exists():
            return "powershell", ps_launcher
        elif bat_launcher.exists():
            return "batch", bat_launcher
    
    elif system in ["linux", "darwin"]:  # Linux or macOS
        sh_launcher = config_dir / "run.sh"
        if sh_launcher.exists():
            return "shell", sh_launcher
    
    # Fallback to Python launcher
    return "python", None

def run_with_launcher(launcher_type, launcher_path, has_microcontroller, microcontroller_port):
    """Run the application using the optimal launcher."""
    # Start serial server if hardware is detected
    if has_microcontroller and microcontroller_port:
        server_started = start_serial_server(microcontroller_port)
        if server_started:
            # Use TCP communication (connects to serial server)
            os.environ["USE_MOCK_COMMUNICATION"] = "false"
            os.environ["SERIAL_SERVER_MODE"] = "true"
            print(f"[CONFIG] Using TCP communication via serial server")
        else:
            print("[WARNING] Serial server failed to start, falling back to mock mode")
            os.environ["USE_MOCK_COMMUNICATION"] = "true"
    else:
        os.environ["USE_MOCK_COMMUNICATION"] = "true"
        print(f"[CONFIG] Using mock communication")
    
    # Filter out conflicting arguments and prepare clean args
    user_args = []
    if len(sys.argv) > 1:
        user_args = [arg for arg in sys.argv[1:] if arg not in ['--mock', '--hardware']]
    
    if launcher_type == "powershell":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(launcher_path)]
        if not has_microcontroller:
            cmd.append("-Mock")
        # Add other user arguments (excluding mock/hardware flags)
        cmd.extend(user_args)
        
    elif launcher_type == "batch":
        cmd = [str(launcher_path)]
        if not has_microcontroller:
            cmd.append("--mock")
        cmd.extend(user_args)
        
    elif launcher_type == "shell":
        cmd = ["bash", str(launcher_path)]
        if not has_microcontroller:
            cmd.append("--mock")
        cmd.extend(user_args)
        
    else:  # Python fallback
        return run_python_launcher(has_microcontroller)
    
    try:
        print(f"[ROCKET] Launching with {launcher_type} launcher...")
        print(f"   Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except Exception as e:
        print(f"[ERROR] Failed to run {launcher_type} launcher: {e}")
        print("   Falling back to Python launcher...")
        return run_python_launcher(has_microcontroller, microcontroller_port)

def run_python_launcher(has_microcontroller, microcontroller_port=None):
    """Fallback Python launcher implementation."""
    try:
        # Add config to Python path
        project_root = Path(__file__).parent
        config_path = project_root / "config"
        sys.path.insert(0, str(config_path))
        
        # Start serial server if hardware is detected
        if has_microcontroller and microcontroller_port:
            server_started = start_serial_server(microcontroller_port)
            if server_started:
                # Use TCP communication (connects to serial server)
                os.environ["USE_MOCK_COMMUNICATION"] = "false"
                os.environ["SERIAL_SERVER_MODE"] = "true"
                print(f"[CONFIG] Using TCP communication via serial server")
            else:
                print("[WARNING] Serial server failed to start, falling back to mock mode")
                os.environ["USE_MOCK_COMMUNICATION"] = "true"
        else:
            os.environ["USE_MOCK_COMMUNICATION"] = "true"
            print(f"[CONFIG] Using mock communication")
        
        # Import and run launcher
        from launcher import main as launcher_main
        
        # Override sys.argv to include mock flag
        if not has_microcontroller and "--mock" not in sys.argv:
            sys.argv.append("--mock")
        
        print("Running with Python launcher...")
        launcher_main()
        return 0
        
    except ImportError as e:
        print(f"[ERROR] Error importing launcher: {e}")
        print("   Make sure you're running from the GUI directory")
        return 1
    except Exception as e:
        print(f"[ERROR] Error running application: {e}")
        return 1

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"\n[SIGNAL] Received signal {signum}, shutting down gracefully...")
        cleanup_serial_server()
        sys.exit(0)
    
    # Handle common termination signals
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    else:
        # Windows uses different signal handling
        signal.signal(signal.SIGINT, signal_handler)
        try:
            signal.signal(signal.SIGTERM, signal_handler)
        except AttributeError:
            pass  # SIGTERM might not be available on Windows

def main():
    """Main entry point with intelligent detection."""
    print("[ROBOT] Cornell Hyperloop GUI - Intelligent Launcher")
    print("=" * 50)
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Setup cache directory
    cache_dir = setup_cache_directory()
    print(f"[FOLDER] Cache directory: {cache_dir}")
    
    # Detect microcontroller
    has_microcontroller, microcontroller_port = detect_microcontroller()
    
    # Detect optimal launcher
    launcher_type, launcher_path = get_optimal_launcher()
    print(f"[TARGET] Detected OS: {platform.system()}")
    print(f"[WRENCH] Using {launcher_type} launcher")
    
    if has_microcontroller:
        print(f"[PLUG] Hardware mode: Connected to {microcontroller_port}")
    else:
        print("[MASK] Mock mode: No microcontroller detected")
    
    print("=" * 50)
    
    # Run the application
    try:
        exit_code = run_with_launcher(launcher_type, launcher_path, has_microcontroller, microcontroller_port)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[STOP] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        # Final fallback
        print("   Attempting direct Python launcher...")
        try:
            exit_code = run_python_launcher(has_microcontroller, microcontroller_port)
            sys.exit(exit_code)
        except:
            sys.exit(1)

if __name__ == "__main__":
    main()