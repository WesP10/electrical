#!/usr/bin/env python3
"""
Cornell Hyperloop GUI - Intelligent Launcher
Usage: python run.py

This launcher automatically detects:
- Operating System (Windows/Linux/MacOS)
- Microcontroller connection status
- Optimal launcher script to use
- Cache directory setup

New team members only need to run: python run.py
"""
import os
import sys
import platform
import subprocess
from pathlib import Path
import serial.tools.list_ports

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
        return run_python_launcher(has_microcontroller)

def run_python_launcher(has_microcontroller):
    """Fallback Python launcher implementation."""
    try:
        # Add config to Python path
        project_root = Path(__file__).parent
        config_path = project_root / "config"
        sys.path.insert(0, str(config_path))
        
        # Set mock environment if needed
        if not has_microcontroller:
            os.environ["USE_MOCK_COMMUNICATION"] = "true"
        
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

def main():
    """Main entry point with intelligent detection."""
    print("[ROBOT] Cornell Hyperloop GUI - Intelligent Launcher")
    print("=" * 50)
    
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
        sys.exit(1)

if __name__ == "__main__":
    main()