"""
Application launcher for the Cornell Hyperloop GUI.
This replaces the various start scripts with a single Python launcher.
"""
import os
import sys
import argparse
from pathlib import Path

# Set up centralized cache directory BEFORE importing any other modules  
config_dir = Path(__file__).parent
project_root = config_dir.parent.parent
cache_dir = project_root / "__pycache__"
os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir)

# Add the config directory to path for environment setup
sys.path.insert(0, str(config_dir))

from environment import setup_environment, get_src_dir

def run_application(use_mock=False, debug=True, host="127.0.0.1", port=8050):
    """Run the main application with specified configuration."""
    # Set up environment
    setup_environment()
    
    # Override specific settings
    if use_mock:
        os.environ["USE_MOCK_COMMUNICATION"] = "true"
    
    os.environ["DASH_DEBUG"] = str(debug).lower()
    os.environ["DASH_HOST"] = host
    os.environ["DASH_PORT"] = str(port)
    
    # Change to source directory
    src_dir = get_src_dir()
    os.chdir(src_dir)
    
    # Import and run the application
    try:
        import app
        print(f"Starting Hyperloop GUI on {host}:{port}")
        print(f"Debug mode: {debug}")
        print(f"Mock communication: {use_mock}")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

def run_tests():
    """Run the test architecture script."""
    setup_environment()
    src_dir = get_src_dir()
    os.chdir(src_dir)
    
    try:
        import test_architecture
        print("Tests completed successfully!")
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(description="Cornell Hyperloop GUI Launcher")
    parser.add_argument("--mock", action="store_true", help="Use mock communication")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8050, help="Port to bind to")
    parser.add_argument("--test", action="store_true", help="Run tests instead of application")
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    else:
        run_application(
            use_mock=args.mock,
            debug=not args.no_debug,
            host=args.host,
            port=args.port
        )

if __name__ == "__main__":
    main()