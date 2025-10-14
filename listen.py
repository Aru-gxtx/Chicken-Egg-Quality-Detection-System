import serial
import time

# --- CONFIGURATION ---
# IMPORTANT: Change this to the port you found in Step 2!
serial_port = '/dev/ttyUSB0' 
baud_rate = 115200 # Must match the Serial.begin() rate in your ESP32 code

# --- MAIN SCRIPT ---
print(f"Attempting to connect to {serial_port} at {baud_rate} baud...")

try:
    # Initialize the serial connection
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    print("Connection successful! Listening for triggers...")
    
    while True:
        # Check if there is data waiting in the buffer
        if ser.in_waiting > 0:
            # Read one line of data from the serial port
            line = ser.readline()
            
            # Decode the bytes into a string and strip whitespace (like \n)
            message = line.decode('utf-8').strip()
            
            # Check if the message is the one we're looking for
            if message == "OBJECT_DETECTED":
                print("✨ TRIGGER RECEIVED! An object was detected by the ESP32.")
                
                # --------------------------------------------------
                # --- YOUR CUSTOM PYTHON ACTION GOES HERE! ---
                #
                # For example, you could:
                # - Control a GPIO pin on the Pi
                # - Run a shell command
                # - Send a network request
                # - Log the event to a file
                #
                # --------------------------------------------------
                
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
