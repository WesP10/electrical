#!/usr/bin/env python3
"""
Simple launcher for the Cornell Hyperloop GUI.
Usage: python run.py [options]
"""
import os
import sys
from pathlib import Path

# Set up centralized cache directory BEFORE importing any modules
project_root = Path(__file__).parent
cache_dir = project_root / "__pycache__"
os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir)

# Add config to path
config_path = project_root / "src" / "config"
sys.path.insert(0, str(config_path))

from launcher import main

if __name__ == "__main__":
    main()