#!/usr/bin/env python3
"""
Cornell Hyperloop GUI - Setup Verification Script

This script verifies that all dependencies are correctly installed and working.
Run this after setting up the environment to catch common issues early.

Usage:
    python verify_setup.py
"""

import sys
import importlib
import traceback
from pathlib import Path

def print_header(title):
    """Print a formatted section header"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_status(test_name, status, details=""):
    """Print test status with consistent formatting"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"   {details}")

def check_python_version():
    """Check Python version compatibility"""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"Python Version: {version_str}")
    
    # Check minimum version (3.9+)
    min_version = (3, 9)
    is_compatible = version[:2] >= min_version
    
    if is_compatible:
        print_status("Python Version", True, f"Version {version_str} is compatible")
    else:
        print_status("Python Version", False, f"Version {version_str} is too old. Minimum: 3.9")
    
    # Check for optimal version (3.11+)
    optimal_version = (3, 11)
    if version[:2] >= optimal_version:
        print_status("Optimal Version", True, f"Version {version_str} supports latest package versions")
    else:
        print_status("Optimal Version", False, f"Consider upgrading to Python 3.11+ for best compatibility")
    
    return is_compatible

def check_core_packages():
    """Check if core packages are installed"""
    print_header("Core Package Installation")
    
    required_packages = {
        'dash': 'Web framework',
        'dash_bootstrap_components': 'UI components',
        'flask': 'Backend framework',
        'numpy': 'Numerical computing',
        'pandas': 'Data processing',
        'plotly': 'Plotting library',
        'requests': 'HTTP library',
        'pyyaml': 'YAML processing'
    }
    
    all_installed = True
    
    for package, description in required_packages.items():
        try:
            importlib.import_module(package)
            print_status(f"{package}", True, description)
        except ImportError:
            print_status(f"{package}", False, f"Missing: {description}")
            all_installed = False
    
    return all_installed

def check_serial_packages():
    """Check serial communication packages and detect conflicts"""
    print_header("Serial Communication Check")
    
    try:
        # Check if we can import serial
        import serial
        print_status("serial module", True, f"Found at: {serial.__file__}")
        
        # Check version
        version = getattr(serial, '__version__', 'Unknown')
        print_status("serial version", True, f"Version: {version}")
        
        # Check if serial.tools exists (critical for our code)
        try:
            import serial.tools
            print_status("serial.tools", True, "Core tools module available")
            
            # Check specific tools we use
            import serial.tools.list_ports
            print_status("serial.tools.list_ports", True, "Port detection available")
            
            # Test port detection
            ports = serial.tools.list_ports.comports()
            port_count = len(ports)
            print_status("Port Detection", True, f"Found {port_count} available ports")
            
            if port_count > 0:
                print("   Available ports:")
                for port in ports[:3]:  # Show first 3 ports
                    print(f"     - {port.device}: {port.description}")
                if port_count > 3:
                    print(f"     ... and {port_count - 3} more")
            
            return True
            
        except ImportError as e:
            print_status("serial.tools", False, f"Missing tools module: {e}")
            print("   This usually means 'serial' package (0.0.97) is installed instead of 'pyserial'")
            print("   Solution: pip uninstall serial && pip install pyserial>=3.5")
            return False
            
    except ImportError as e:
        print_status("serial module", False, f"Cannot import serial: {e}")
        print("   Solution: pip install pyserial>=3.5")
        return False

def check_package_conflicts():
    """Check for known package conflicts"""
    print_header("Package Conflict Detection")
    
    try:
        import pkg_resources
        installed_packages = {pkg.project_name.lower(): pkg.version 
                            for pkg in pkg_resources.working_set}
        
        # Check for serial conflict
        has_pyserial = 'pyserial' in installed_packages
        has_serial = 'serial' in installed_packages
        
        if has_pyserial and not has_serial:
            print_status("Serial packages", True, f"pyserial {installed_packages['pyserial']} (correct)")
        elif has_serial and not has_pyserial:
            print_status("Serial packages", False, f"serial {installed_packages['serial']} (wrong package)")
            print("   Solution: pip uninstall serial && pip install pyserial>=3.5")
        elif has_pyserial and has_serial:
            print_status("Serial packages", False, "Both pyserial and serial installed (conflict)")
            print(f"   pyserial: {installed_packages['pyserial']}")
            print(f"   serial: {installed_packages['serial']}")
            print("   Solution: pip uninstall serial")
        else:
            print_status("Serial packages", False, "No serial communication package found")
            print("   Solution: pip install pyserial>=3.5")
        
        return has_pyserial and not has_serial
        
    except ImportError:
        print_status("Package conflict check", False, "pkg_resources not available")
        return True  # Can't check, assume OK

def check_project_structure():
    """Check if we're in the right directory and files exist"""
    print_header("Project Structure Check")
    
    current_dir = Path.cwd()
    gui_dir = current_dir if current_dir.name == 'GUI' else current_dir / 'GUI'
    
    expected_files = [
        'requirements.txt',
        'run.py',
        'src/app.py',
        'config/settings.py'
    ]
    
    all_found = True
    
    print(f"Current directory: {current_dir}")
    print(f"Looking for GUI files in: {gui_dir}")
    
    for file_path in expected_files:
        full_path = gui_dir / file_path
        exists = full_path.exists()
        print_status(file_path, exists, f"Path: {full_path}")
        if not exists:
            all_found = False
    
    return all_found

def check_imports_used_in_code():
    """Test importing modules that are actually used in the codebase"""
    print_header("Code-Specific Import Check")
    
    # These are the actual imports used in the codebase
    test_imports = [
        ('serial', 'Basic serial module'),
        ('serial.tools.list_ports', 'Port detection (used in run.py, port_detection.py)'),
        ('dash', 'Web framework (used in app.py)'),
        ('dash_bootstrap_components', 'UI components (used throughout)'),
        ('plotly.graph_objects', 'Plotting (used in sensor displays)'),
        ('pandas', 'Data processing (used in data handling)'),
        ('numpy', 'Numerical operations (used in calculations)'),
    ]
    
    all_imports_work = True
    
    for import_name, description in test_imports:
        try:
            importlib.import_module(import_name)
            print_status(import_name, True, description)
        except ImportError as e:
            print_status(import_name, False, f"{description} - Error: {e}")
            all_imports_work = False
    
    return all_imports_work

def run_verification():
    """Run all verification checks"""
    print("Cornell Hyperloop GUI - Setup Verification")
    print(f"Running from: {Path.cwd()}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Core Packages", check_core_packages),
        ("Serial Communication", check_serial_packages),
        ("Package Conflicts", check_package_conflicts),
        ("Project Structure", check_project_structure),
        ("Code Imports", check_imports_used_in_code)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(check_name, False, f"Check failed with error: {e}")
            if '--debug' in sys.argv:
                traceback.print_exc()
            results[check_name] = False
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, passed_check in results.items():
        status_symbol = "✅" if passed_check else "❌"
        print(f"{status_symbol} {check_name}")
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if all(results.values()):
        print("\n🎉 All checks passed! Your setup is ready.")
        print("You can now run: python run.py")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        print("See SETUP_TROUBLESHOOTING.md for detailed solutions.")
        
        # Specific guidance for common issues
        if not results.get("Serial Communication", True):
            print("\n🔧 Quick fix for serial issues:")
            print("   pip uninstall serial")
            print("   pip install pyserial>=3.5")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)