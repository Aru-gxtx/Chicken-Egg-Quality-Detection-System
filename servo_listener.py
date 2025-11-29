import serial
import time

serial_port = '/dev/ttyUSB0' 
baud_rate = 115200 # Must match the Serial.begin() rate in your ESP32 code

print(f"Attempting to connect to {serial_port} at {baud_rate} baud...")

try:
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    print("Connection successful! Listening for triggers...")
    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline()
            
            message = line.decode('utf-8').strip()
            
            if message == "OBJECT_DETECTED":
                print("✨ TRIGGER RECEIVED! An object was detected by the ESP32.")
                
            elif message == "OBJECT_GONE":
                print("Object is no longer detected.")

except serial.SerialException as e:
    print(f"Error: Could not open serial port {serial_port}.")
    print(f"Details: {e}")
    print("Please check the port name and ensure the ESP32 is connected.")
    print("You may also need to run 'sudo usermod -a -G dialout $USER' and reboot.")

except KeyboardInterrupt:
    print("\nProgram stopped by user.")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed.")
