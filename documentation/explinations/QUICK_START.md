# Quick Start Guide - Serial Communication

## 🚀 Quick Test (No Hardware Needed)

```powershell
cd "C:\Users\Westo\Saved Games\electrical\GUI"
python run.py
```

**You should see:**
- GUI opens in browser
- 3 sensors appear within 1 second:
  - `temperature`
  - `accelerometer`  
  - `pressure`
- Charts update smoothly (10Hz)
- All sensors show as "Available"

This is **mock mode** - simulated sensor data for testing.

---

## 🔌 Connect Real Hardware

### Step 1: Upload Arduino Code

**Any sketch that prints this format works:**

```cpp
// Minimal example - just print the format!
void setup() {
  Serial.begin(9600);
}

void loop() {
  // Header every 10 messages
  static int count = 0;
  if (count % 10 == 0) {
    Serial.println("*H*_temperature_A0_temp:25.5C");
  } else {
    Serial.println("temperature:25.5");
  }
  count++;
  delay(100);  // 10Hz
}
```

### Step 2: Find Your COM Port

**Windows:**
1. Open Device Manager
2. Expand "Ports (COM & LPT)"
3. Look for "Arduino" or "USB Serial Port"
4. Note the COM number (e.g., COM3)

### Step 3: Configure GUI

**Option A: Environment Variable (Recommended)**
```powershell
$env:SERIAL_PORT = "COM3"  # Replace COM3 with your port
python run.py
```

**Option B: Edit Settings File**

Edit `config/settings.py`:
```python
port: str = 'COM3'  # Change from 'loop://' to your COM port
baudrate: int = 9600
```

Then run:
```powershell
python run.py
```

### Step 4: Verify

✅ GUI starts with 0 sensors  
✅ Within 1-2 seconds, `temperature` sensor appears  
✅ Data updates at 10Hz  
✅ Sensor shows as "Available"  

---

## 📋 Message Format Reference

### Header (Discovery)
```
*H*_sensorName_pinList_payload\n
```

**Examples:**
```
*H*_temperature_A0_temp:25.5C
*H*_accelerometer_A1,D2,D3_x:0.02,y:-0.01,z:9.81
*H*_pressure_A2_pressure:1013.25hPa
*H*_ultrasonic_D7_distance:150cm
*H*_gps_Serial1_lat:42.44,lon:-76.48
```

### Data (Updates)
```
sensorName:value1,value2,...\n
```

**Examples:**
```
temperature:25.6
accelerometer:0.03,-0.02,9.80
pressure:1013.30
ultrasonic:151.2
gps:42.4405,-76.4833
```

---

## 🎯 Key Rules

1. **Headers announce sensors** - Send on startup and periodically (every 10th message)
2. **Data messages are fast** - Send between headers for high-frequency updates
3. **Always end with newline** - `\n` or `Serial.println()`
4. **Use consistent names** - Same `sensorName` in headers and data
5. **Pins are informational** - GUI doesn't control pins, just displays them

---

## 🐛 Debugging

### Check Recent Serial Output

Add this to your code:

```python
from core.dependencies import container
from services.communication_service import CommunicationService

comm_service = container.get(CommunicationService)
lines = comm_service.get_buffer_lines(20)
print("Last 20 serial lines:")
for line in lines:
    print(f"  {line}")
```

### Enable Debug Logging

Edit `config/log_config.py`:
```python
logger.setLevel(logging.DEBUG)  # Change from INFO
```

This will show:
- Every line received from serial
- Header parsing details
- Sensor discovery events
- Connection status

---

## ⚙️ Configuration

**File:** `config/settings.py`

```python
@dataclass
class CommunicationConfig:
    port: str = 'loop://'      # 'loop://' = mock, 'COM3' = real
    baudrate: int = 9600       # Match Arduino Serial.begin()
    timeout: int = 1000        # Read timeout (milliseconds)
    use_mock: bool = False     # Force mock mode
```

**Environment Variables:**
```powershell
$env:SERIAL_PORT = "COM3"
$env:SERIAL_BAUDRATE = "9600"
$env:USE_MOCK_COMMUNICATION = "false"
```

---

## 📊 Architecture at a Glance

```
┌──────────────────────────────────────┐
│         Your Arduino Sketch          │
│  Serial.println("*H*_temp_A0_...")   │
│  Serial.println("temp:25.5")         │
└────────────────┬─────────────────────┘
                 │ USB Serial (9600 baud)
                 ▼
┌──────────────────────────────────────┐
│    PySerialCommunication Thread      │
│  - read_until('\n')                  │
│  - Decode UTF-8                      │
│  - Add to buffer                     │
│  - Parse header/data                 │
└────────────────┬─────────────────────┘
                 │ Callbacks
                 ▼
┌──────────────────────────────────────┐
│         SensorService                │
│  - Create DynamicSensor              │
│  - Update sensor data                │
│  - Manage watchdog timers            │
└────────────────┬─────────────────────┘
                 │ Data updates
                 ▼
┌──────────────────────────────────────┐
│              GUI                     │
│  - Display sensors                   │
│  - Update charts                     │
│  - Show availability                 │
└──────────────────────────────────────┘
```

**Key Point:** The serial reading thread never blocks the GUI!

---

## 🎓 Examples

### Multiple Sensors

```cpp
void loop() {
  static int count = 0;
  
  // Temperature
  float temp = readTemp();
  if (count % 10 == 0) {
    Serial.println("*H*_temperature_A0_temp:" + String(temp) + "C");
  } else {
    Serial.println("temperature:" + String(temp));
  }
  
  // Pressure
  float pressure = readPressure();
  if (count % 10 == 0) {
    Serial.println("*H*_pressure_A1_pressure:" + String(pressure) + "hPa");
  } else {
    Serial.println("pressure:" + String(pressure));
  }
  
  count++;
  delay(100);
}
```

### Multi-Value Sensors

```cpp
void loop() {
  static int count = 0;
  
  float x = readAccelX();
  float y = readAccelY();
  float z = readAccelZ();
  
  if (count % 10 == 0) {
    Serial.println("*H*_accelerometer_A1,A2,A3_x:" + String(x) + 
                   ",y:" + String(y) + ",z:" + String(z));
  } else {
    Serial.println("accelerometer:" + String(x) + "," + 
                   String(y) + "," + String(z));
  }
  
  count++;
  delay(10);  // 100Hz
}
```

---

## ✅ Success Checklist

Before you start:
- [ ] Arduino connected via USB
- [ ] COM port identified
- [ ] Sketch uploaded (printing format)
- [ ] Baud rate matches (9600)

When you run `python run.py`:
- [ ] GUI opens in browser
- [ ] Sensors appear (not "5 sensors" hardcoded)
- [ ] Data updates smoothly
- [ ] No lag or freezing
- [ ] Sensors show "Available"

Disconnect/Reconnect test:
- [ ] Unplug Arduino
- [ ] Wait 5 seconds
- [ ] Sensors show "Unavailable"
- [ ] Plug back in
- [ ] Sensors become "Available" again

---

## 📚 Full Documentation

- **IMPLEMENTATION_SUMMARY.md** - Overview of changes
- **SERIAL_COMMUNICATION_ARCHITECTURE.md** - Detailed technical docs
- **QUICK_START.md** - This file

**Questions? Check the buffer:**
```python
lines = comm_service.get_buffer_lines(50)
```

This shows exactly what the GUI is receiving from the serial port!

---

**Happy sensing! 🎉**
