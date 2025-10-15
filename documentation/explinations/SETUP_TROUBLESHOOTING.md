# Setup Troubleshooting Guide

This guide helps resolve common setup issues encountered when cloning and running the Cornell Hyperloop GUI.

## Quick Setup (Recommended)

```bash
cd GUI
python run.py
```

## Common Issues

### 1. ImportError: No module named 'serial.tools'

**Symptoms:**
```
ImportError: No module named 'serial.tools'
ModuleNotFoundError: No module named 'serial.tools.list_ports'
```

**Cause:**
This happens when the wrong `serial` package is installed. There are two different packages:
- `pyserial` (correct) - Provides `serial` module with `serial.tools.list_ports`
- `serial==0.0.97` (incorrect) - Also provides `serial` module but lacks `serial.tools`

**Solution:**
```bash
# Check what's installed
pip list | grep -i serial

# If you see 'serial' (not pyserial), remove it:
pip uninstall serial

# Install the correct package
pip install pyserial>=3.5

# Verify installation
python -c "import serial.tools.list_ports; print('Success!')"
```

### 2. Virtual Environment Issues

**Problem:** Dependencies not found even after installation

**Solution:**
Make sure you're in the correct virtual environment:

```bash
# Windows
cd GUI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
cd GUI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Python Version Compatibility

**Problem:** Package installation fails or incompatible versions

**Requirements:**
- Python 3.9 or higher recommended
- Python 3.11+ for latest package versions

**Check your version:**
```bash
python --version
```

### 4. Port Permission Issues (Linux/macOS)

**Problem:** Cannot access serial ports

**Solution:**
```bash
# Add user to dialout group (Linux)
sudo usermod -a -G dialout $USER

# Then log out and back in, or:
newgrp dialout
```

### 5. Windows PowerShell Execution Policy

**Problem:** Cannot run scripts on Windows

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Verification Script

Run this to verify your installation:

```bash
python verify_setup.py
```

This will check:
- Python version compatibility
- All required packages are installed
- Serial communication modules work
- Port detection functionality

## Package Conflicts

### Serial Package Conflict
**Never install both `pyserial` and `serial` packages simultaneously**

| Package | Status | Description |
|---------|--------|-------------|
| `pyserial>=3.5` | ✅ REQUIRED | Official serial communication library |
| `serial==0.0.97` | ❌ FORBIDDEN | Conflicts with pyserial, lacks serial.tools |

### How to Check for Conflicts

```bash
# List all serial-related packages
pip list | grep -i serial

# Expected output:
pyserial    3.5

# Problem output (contains both):
pyserial    3.5
serial      0.0.97
```

### How to Fix Conflicts

```bash
# Remove conflicting packages
pip uninstall serial pyserial

# Reinstall correct package
pip install pyserial>=3.5
```

## Advanced Troubleshooting

### Clean Installation

If you're having persistent issues:

```bash
# Remove virtual environment
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Create fresh environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install fresh dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Debug Mode

Run with debug information:

```bash
python run.py --debug
```

### Check Hardware Detection

Test hardware detection without running the full GUI:

```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Found port: {port.device} - {port.description}")
```

## Getting Help

1. **First**, try the verification script: `python verify_setup.py`
2. **Check** this troubleshooting guide for your specific error
3. **Verify** you have the correct packages installed (especially pyserial)
4. **Contact** team leads if issues persist

## Common Error Messages and Solutions

| Error Message | Solution |
|---------------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `pip install pyserial>=3.5` |
| `ImportError: No module named 'serial.tools'` | Uninstall `serial`, install `pyserial` |
| `Permission denied: '/dev/ttyUSB0'` | Add user to dialout group (Linux) |
| `Access is denied` (Windows) | Run as administrator or check antivirus |
| `dash not found` | `pip install -r requirements.txt` |

---

**Last Updated:** October 2025  
**For Issues:** Contact Cornell Hyperloop Electrical Team