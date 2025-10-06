# Serial Communication Architecture

## Overview

The GUI uses a **passive listening approach** to detect sensors. Any microcontroller printing to the configured serial port and baud rate will have its output automatically detected and parsed.

## Key Design Principles

1. **Passive Discovery** - No commands sent to the microcontroller. GUI just listens.
2. **Thread-Safe** - Serial reading happens on a separate thread to prevent GUI lag.
3. **Line Buffering** - Uses `read_until('\n')` for efficient line-by-line parsing.
4. **Format Agnostic** - GUI doesn't care about Arduino code, only serial output format.

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    (app.py, sensor_service.py)          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      CommunicationService               │
│   (High-level facade/wrapper)           │
└────────────────┬────────────────────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│PySerialComm  │    │MockCommunication │
│(Real Serial) │    │(Simulated Data)  │
└──────┬───────┘    └────────┬─────────┘
       │                     │
       ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│Serial Thread │    │Mock Data Thread │
│read_until()  │    │Simulated Output │
└──────────────┘    └─────────────────┘
```

---

## Communication Service (`communication_service.py`)

### `BaseCommunication` (Abstract Base Class)

All communication implementations inherit from this.

**Methods:**
- `start()` - Start the communication
- `stop()` - Stop the communication
- `close()` - Cleanup resources
- `set_discovery_callback(callback)` - Set sensor discovery callback
- `register_data_callback(sensor_name, callback)` - Register data callback
- `deregister_data_callback(sensor_name)` - Remove data callback
- `get_discovered_sensors()` - Get list of sensor names
- `get_buffer_lines(n)` - Get last n lines from buffer

### `PySerialCommunication`

**Real hardware serial communication.**

**Features:**
- Uses `pyserial` library
- Runs on separate thread (`SerialReadThread`)
- Uses `read_until(b'\n')` for line-based reading
- Automatic reconnection on errors
- Line buffering with configurable size
- Thread-safe with proper cleanup

**Flow:**
1. `start()` → Connects to serial port → Starts read thread
2. Thread continuously reads lines using `read_until('\n')`
3. Each line decoded from UTF-8 (errors ignored)
4. Lines added to buffer (FIFO, limited size)
5. Lines processed for headers or data
6. Callbacks triggered for discovered sensors/data

**Configuration:**
```python
PySerialCommunication(
    port='COM3',           # Serial port
    baudrate=9600,         # Baud rate
    timeout=1.0,           # Read timeout in seconds
    buffer_size=100        # Max lines in buffer
)
```

### `MockCommunication`

**Simulated sensor data for testing.**

**Features:**
- No hardware required
- Simulates 3 sensors: temperature, accelerometer, pressure
- Generates realistic random data
- Sends headers every 10th message
- Same interface as PySerialCommunication

**Simulated Sensors:**
- `temperature` - Pin A0, temp value in Celsius
- `accelerometer` - Pins A1,D2,D3, x,y,z values
- `pressure` - Pin A2, pressure in hPa

### `CommunicationService` (Facade)

**High-level wrapper used by the application.**

**Responsibilities:**
- Chooses between `PySerialCommunication` or `MockCommunication` based on config
- Provides unified interface
- Handles initialization and cleanup

**Usage:**
```python
from config.settings import load_config
from services.communication_service import CommunicationService

config = load_config()
comm_service = CommunicationService(config.communication)

# Set discovery callback
comm_service.set_discovery_callback(on_sensor_discovered)

# Register data callback
comm_service.register_data_callback('temperature', on_temp_data)

# Cleanup
comm_service.close()
```

---

## Serial Output Format

The GUI expects two types of messages:

### 1. Header Message (Discovery)

**Format:**
```
*H*_sensorName_pinList_payload\n
```

**Parts:**
- `*H*_` - Header marker (literal)
- `sensorName` - Unique identifier (e.g., "temperature")
- `pinList` - Comma-separated pins (e.g., "A0" or "A1,D2,D3")
- `payload` - Initial data value (e.g., "temp:25.5C")

**Examples:**
```
*H*_temperature_A0_temp:25.5C
*H*_accelerometer_A1,D2,D3_x:0.02,y:-0.01,z:9.81
*H*_pressure_A2_pressure:1013.25hPa
*H*_ultrasonic_D7_distance:150cm
```

**When to send:**
- On startup (sensor announces itself)
- Periodically as a "keepalive" (e.g., every 10th message)
- After reconnection

### 2. Data Message (Fast Updates)

**Format:**
```
sensorName:value1,value2,...\n
```

**Examples:**
```
temperature:25.6
accelerometer:0.03,-0.02,9.80
pressure:1013.30
ultrasonic:151.2
```

**When to send:**
- Regular updates at desired frequency (e.g., 10Hz)
- More compact than headers (faster transmission)

---

## Arduino Example

```cpp
// Configuration
const int TEMP_PIN = A0;
const int UPDATE_INTERVAL = 100;  // ms (10Hz)
const int HEADER_INTERVAL = 10;   // Send header every 10th message

int messageCount = 0;

void setup() {
  Serial.begin(9600);
  pinMode(TEMP_PIN, INPUT);
  delay(1000);  // Let serial stabilize
}

void loop() {
  // Read sensor
  int rawValue = analogRead(TEMP_PIN);
  float temperature = (rawValue / 1024.0) * 100.0;  // Example conversion
  
  // Send header every 10th message, otherwise send data
  if (messageCount % HEADER_INTERVAL == 0) {
    // Header format: *H*_sensorName_pinList_payload
    Serial.print("*H*_temperature_A0_temp:");
    Serial.print(temperature, 2);
    Serial.println("C");
  } else {
    // Data format: sensorName:value
    Serial.print("temperature:");
    Serial.println(temperature, 2);
  }
  
  messageCount++;
  delay(UPDATE_INTERVAL);
}
```

---

## Threading Model

### Serial Reading Thread

**Thread Name:** `SerialReadThread`
**Daemon:** Yes (exits when main program exits)
**Purpose:** Continuously read from serial port

**Lifecycle:**
1. Created when `start()` is called
2. Runs `_read_loop()` method
3. Stops when `running` flag set to False
4. Joined during `stop()` call

**Thread Safety:**
- Line buffer uses `collections.deque` (thread-safe for append/pop)
- Callbacks executed on serial thread (keep them fast!)
- Serial connection uses timeouts to prevent blocking

### Mock Data Thread

**Thread Name:** `MockDataThread`
**Similar to serial thread but generates simulated data**

---

## Data Flow

### Discovery Flow

```
1. Arduino prints: "*H*_temperature_A0_temp:25.5C\n"
2. SerialReadThread reads complete line
3. Line added to buffer
4. _parse_header() extracts: name="temperature", pins=["A0"]
5. Check if new sensor → Yes
6. Add to discovered_sensors dict
7. Call discovery_callback("temperature", ["A0"], "temp:25.5C")
8. SensorService creates DynamicSensor object
9. GUI updates to show new sensor
```

### Data Flow

```
1. Arduino prints: "temperature:25.6\n"
2. SerialReadThread reads complete line
3. Line added to buffer
4. _parse_data() extracts: name="temperature", values=["25.6"]
5. Update last_seen timestamp
6. Call data_callback("temperature", ["25.6"])
7. SensorService updates sensor data
8. GUI chart updates
```

---

## Buffer Management

**Purpose:** Keep recent serial output for debugging

**Implementation:**
- `collections.deque(maxlen=buffer_size)`
- FIFO (First In, First Out)
- Automatically drops oldest when full
- Thread-safe for single reader/single writer

**Usage:**
```python
# Get last 10 lines
recent_lines = comm_service.get_buffer_lines(10)
for line in recent_lines:
    print(line)
```

---

## Error Handling

### Connection Errors

**Scenario:** Serial port not available or disconnected

**Handling:**
- Log error message
- Wait 2 seconds
- Attempt reconnection
- Repeat until successful or service stopped

### Decode Errors

**Scenario:** Invalid UTF-8 bytes received

**Handling:**
- Use `decode('utf-8', errors='ignore')`
- Skip malformed lines
- Log debug message
- Continue reading

### Parse Errors

**Scenario:** Invalid message format

**Handling:**
- Log warning with the invalid line
- Skip the message
- Continue reading next line

---

## Configuration

**File:** `config/settings.py`

```python
@dataclass
class CommunicationConfig:
    port: str = 'loop://'           # Serial port or 'loop://' for mock
    baudrate: int = 9600            # Baud rate (9600, 115200, etc.)
    timeout: int = 1000             # Timeout in milliseconds
    use_mock: bool = False          # Force mock mode
```

**Environment Variables:**
- `SERIAL_PORT` - Override serial port
- `SERIAL_BAUDRATE` - Override baud rate
- `SERIAL_TIMEOUT` - Override timeout
- `USE_MOCK_COMMUNICATION` - Set to 'true' for mock mode

**Mock Mode Triggered When:**
- `use_mock = True`
- `port = 'loop://'`
- `port` starts with 'mock'

---

## Testing

### With Mock Data

```bash
cd "C:\Users\Westo\Saved Games\electrical\GUI"
python run.py
```

Should see 3 sensors discovered within 1 second.

### With Real Hardware

1. Connect Arduino to USB
2. Identify COM port (Device Manager on Windows)
3. Set environment variable:
   ```powershell
   $env:SERIAL_PORT = "COM3"
   $env:SERIAL_BAUDRATE = "9600"
   ```
4. Run GUI:
   ```bash
   python run.py
   ```

---

## Debugging

### Check Buffer

```python
lines = comm_service.get_buffer_lines(20)
print("Recent serial output:")
for line in lines:
    print(f"  {line}")
```

### Check Discovered Sensors

```python
sensors = comm_service.get_discovered_sensors()
print(f"Discovered: {sensors}")
```

### Enable Debug Logging

**File:** `config/log_config.py`

Change level to DEBUG:
```python
logger.setLevel(logging.DEBUG)
```

---

## Advantages of This Design

✅ **Simple Arduino Code** - Just print data, no complex protocol
✅ **No Commands** - Passive listening, no active querying
✅ **Thread-Safe** - Serial reading won't block GUI
✅ **Buffered** - Can review recent output for debugging
✅ **Auto-Reconnect** - Handles USB disconnect/reconnect
✅ **Format-Driven** - Any device printing the format works
✅ **Testable** - Mock mode for development without hardware
✅ **Scalable** - Handle multiple sensors at high frequency

---

## Performance

**Serial Reading:**
- Blocking `read_until()` with 1.0s timeout
- Minimal CPU usage when idle
- Fast response when data arrives

**Data Rate:**
- Tested up to 100Hz per sensor
- Limited by baud rate and message size
- 9600 baud ≈ 960 bytes/sec ≈ 50-100 messages/sec

**GUI Impact:**
- Serial reading on separate thread → No GUI lag
- Callbacks should be fast (just update data, don't compute)
- Heavy processing should be deferred or batched

---

## Migration Notes

**Old Approach:**
- GUI sent `GET_SENSORS` command
- Arduino responded with sensor list
- Complex protocol with handshaking

**New Approach:**
- GUI passively listens
- Arduino just prints data
- Headers contain sensor info

**Benefits:**
- Simpler Arduino code
- More robust (no protocol sync issues)
- Works with any device (not just Arduino)
- Easier to test with serial terminal
