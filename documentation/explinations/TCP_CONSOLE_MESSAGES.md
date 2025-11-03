# TCP Console Messages - Explanation Guide

This document explains the different types of messages you'll see in the TCP Communication Console on the Sensors page.

## Message Format

Each console line follows this format:
```
[TIMESTAMP] [TYPE ] Message Content
```

- **TIMESTAMP**: Time in `HH:MM:SS.mmm` format (24-hour clock with milliseconds)
- **TYPE**: One of `SEND`, `RECV`, `INFO`, or `ERROR`
- **Message Content**: The actual data being transmitted or status information

---

## Message Types

### 1. **[INFO] Messages** (Yellow/Gold Color: `#dcdcaa`)

These are informational status messages about the connection state.

**Examples:**
```
14:23:45.123 [INFO ] Connecting to localhost:9999...
14:23:45.234 [INFO ] Connected to serial server
```

**What they mean:**
- `Connecting to...`: The GUI is attempting to establish a TCP connection to the serial server
- `Connected to serial server`: Successfully connected to the serial server (running on port 9999)

---

### 2. **[SEND] Messages** (Teal Color: `#4ec9b0`)

These are requests being **sent FROM the GUI TO the serial server**.

**Examples:**
```
14:23:47.001 [SEND ] {"type": "get_data", "request_id": 1}
```

**Common SEND message types:**

#### `get_data` - Data Request
```json
{"type": "get_data", "request_id": 123}
```
- **Purpose**: GUI is requesting sensor data from the serial server
- **request_id**: Unique identifier to match request with response
- The GUI sends these periodically (every ~0.5-2 seconds) to poll for new sensor data

---

### 3. **[RECV] Messages** (Blue Color: `#569cd6`)

These are responses being **received BY the GUI FROM the serial server**.

**Examples:**
```
14:23:47.015 [RECV ] {"type": "data_response", "data_count": 3, "request_id": 1}
14:23:49.012 [RECV ] {"type": "periodic_update", "data_count": 5}
14:23:50.100 [RECV ] {"type": "server_status", "serial_connected": true, "sensors": 3}
```

**Common RECV message types:**

#### `periodic_update` - Automatic Data Push
```json
{"type": "periodic_update", "data_count": 5}
```
- **Purpose**: The serial server is automatically pushing new sensor data to the GUI
- **data_count**: Number of data entries (discoveries + sensor readings) in this update
- These arrive automatically without the GUI requesting them
- **Contains**: New sensor discoveries and recent sensor data readings

#### `data_response` - Response to Request
```json
{"type": "data_response", "data_count": 3, "request_id": 1}
```
- **Purpose**: Response to a GUI's `get_data` request
- **data_count**: Number of data entries being sent
- **request_id**: Matches the original request ID
- **Contains**: Historical sensor data within the requested time range

#### `server_status` - Server Status Update
```json
{"type": "server_status", "serial_connected": true, "sensors": 3}
```
- **Purpose**: Provides current status of the serial server
- **serial_connected**: Whether the serial server has an active connection to Arduino/microcontroller
  - `true`: Serial port is open and reading data
  - `false`: No serial device connected
- **sensors**: Number of sensors currently discovered by the serial server

---

### 4. **[ERROR] Messages** (Red Color: `#f48771`)

These indicate problems or failures in the communication.

**Examples:**
```
14:23:50.500 [ERROR] Connection failed: [WinError 10061] No connection could be made
14:23:51.000 [ERROR] Server closed connection
14:23:52.000 [ERROR] Invalid JSON: {"broken":...
```

**Common ERROR types:**

#### Connection Errors
- `Connection failed: [WinError 10061]`: Serial server is not running on port 9999
- `Server closed connection`: The serial server stopped or crashed
- `Unexpected error: ...`: General connection problems

#### Data Errors
- `Invalid JSON: ...`: Received malformed data that couldn't be parsed
  - Usually indicates communication corruption or protocol mismatch

---

## Data Flow Example

Here's a typical sequence you'll see when everything is working:

```
1. 14:23:45.123 [INFO ] Connecting to localhost:9999...
   → GUI attempts to connect to serial server

2. 14:23:45.234 [INFO ] Connected to serial server
   → Connection successful

3. 14:23:47.001 [SEND ] {"type": "get_data", "request_id": 1}
   → GUI requests data from serial server

4. 14:23:47.015 [RECV ] {"type": "data_response", "data_count": 3, "request_id": 1}
   → Serial server responds with 3 data entries

5. 14:23:49.012 [RECV ] {"type": "periodic_update", "data_count": 5}
   → Serial server pushes new data automatically (5 entries)

6. 14:23:49.100 [RECV ] {"type": "server_status", "serial_connected": true, "sensors": 3}
   → Status update: Arduino connected, 3 sensors discovered

7. 14:23:51.001 [SEND ] {"type": "get_data", "request_id": 2}
   → GUI requests more data

8. 14:23:51.015 [RECV ] {"type": "data_response", "data_count": 2, "request_id": 2}
   → Serial server responds with 2 new entries
```

---

## What's Inside the Data?

The console shows **simplified** JSON to keep it readable. The actual data contains:

### In `periodic_update` and `data_response`:
```json
{
  "type": "periodic_update",
  "data": [
    {
      "type": "discovery",
      "sensor_name": "Ultrasonic Sensor",
      "pins": [7],
      "payload": "DISCOVERY:Ultrasonic Sensor:7",
      "timestamp": 1730304225.123
    },
    {
      "type": "sensor_data",
      "sensor_name": "Ultrasonic Sensor",
      "values": [15.3],
      "timestamp": 1730304225.456
    }
  ]
}
```

**Entry types in data array:**

1. **`discovery` entries**: New sensor detected
   - `sensor_name`: Human-readable sensor name
   - `pins`: Arduino pins the sensor is connected to
   - `payload`: Raw discovery string from Arduino
   - `timestamp`: When the sensor was first discovered

2. **`sensor_data` entries**: Actual sensor readings
   - `sensor_name`: Which sensor this data is from
   - `values`: Array of sensor values (e.g., `[15.3]` for distance in cm)
   - `timestamp`: When the reading was taken

---

## Troubleshooting with the Console

### No messages at all
- ✅ **Solution**: Start the serial server with `python src/services/serial_server.py --auto-detect`

### Only seeing `Connecting to localhost:9999...` repeatedly
- ❌ **Problem**: Serial server is not running
- ✅ **Solution**: Start the serial server in a separate terminal

### Seeing `[ERROR] Connection failed`
- ❌ **Problem**: Serial server not running or wrong port
- ✅ **Solution**: Check that serial server is running on port 9999

### Seeing `server_status` with `"serial_connected": false`
- ❌ **Problem**: Serial server is running but Arduino is not connected
- ✅ **Solution**: 
  - Check Arduino is plugged in via USB
  - Check Arduino is sending data (upload correct sketch)
  - Restart serial server with `--auto-detect` to find the port

### Messages arriving but no sensor graphs updating
- ❌ **Problem**: Data format mismatch or sensor not registered
- ✅ **Solution**: Check that `sensor_name` in console matches registered sensor names

---

## Summary

- **[INFO]**: Connection status updates
- **[SEND]**: Requests from GUI → Serial Server (you're asking for data)
- **[RECV]**: Responses from Serial Server → GUI (you're receiving data)
- **[ERROR]**: Something went wrong

The console updates every 2 seconds and shows the last 50 messages. It auto-scrolls to show the most recent activity at the bottom.
