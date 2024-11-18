import serial
import threading
import time
def start_sensor_simulation(port, baudrate, timeout):
    def sensor_writer():
        # Open a new serial connection to the same loop:// port
        with serial.serial_for_url(port, baudrate=baudrate, timeout=timeout) as ser:
            while True:
                # Simulate accelerometer sensor data
                sensor_id = "ACCEL_SENSOR"
                data_values = f"{sensor_id}:1.23,4.56,7.89\n"
                ser.write(data_values.encode('utf-8'))  # Write to the port
                print(f"Sent: {data_values.strip()}")
                time.sleep(.5)  # Send data every second
    # Start the sensor writer thread
    writer_thread = threading.Thread(target=sensor_writer, daemon=True)
    writer_thread.start()