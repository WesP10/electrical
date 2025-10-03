#!/usr/bin/env python3
"""Test script for the refactored architecture."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all major imports."""
    try:
        from config.settings import load_config
        print('✓ Config module imported successfully')
        
        from config.log_config import setup_logging
        print('✓ Logging module imported successfully')
        
        from core.application import HyperloopGUIApplication
        print('✓ Application module imported successfully')
        
        from services.communication_service import CommunicationService
        print('✓ Communication service imported successfully')
        
        from services.sensor_service import SensorService
        print('✓ Sensor service imported successfully')
        
        from services.profile_service import ProfileService
        print('✓ Profile service imported successfully')
        
        from ui.layout import MainLayout
        print('✓ UI layout imported successfully')
        
        print('\n✅ All core modules imported successfully!')
        
        # Test configuration loading
        config = load_config()
        print(f'✓ Configuration loaded: {config.title}')
        
        return True
        
    except Exception as e:
        print(f'❌ Error importing modules: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)