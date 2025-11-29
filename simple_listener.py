import serial
import time

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

def main():
    ser = None
    print(f"--- Servo Angle Tuner ---")
    print("This script will send raw angles (0-180) to your ESP32.")
    print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
        print("✅ Connection successful.")
        print("Type an angle (e.g., '90') and press Enter.")
        print("Type 'q' or 'quit' to exit.")
        print("-" * 28)

        time.sleep(2) 

        while True:
            command = input("Enter angle (0-180) or 'q' to quit: ").strip()

            if command.lower() == 'q' or command.lower() == 'quit':
                print("Exiting tuner.")
                break
            
            try:
                angle = int(command)
                
                if 0 <= angle <= 180:
                    serial_command = f"{angle}\n"
                    
                    ser.write(serial_command.encode('utf-8'))
                    print(f"  -> Sent angle: {angle}")
                    
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print(f"  <- ESP32 says: {response}")

                else:
                    print(f"[ERROR] Angle must be between 0 and 180. You typed: {angle}")

            except ValueError:
                print(f"[ERROR] Invalid input. Please type a number (0-180) or 'q'.")

    except serial.SerialException as e:
        print(f"❌ SERIAL ERROR: Could not open port {SERIAL_PORT}.")
        print(f"   Details: {e}")
        print(f"   Is the ESP32 plugged in? Is another program (like Arduino Monitor) using it?")
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == '__main__':
    main()
