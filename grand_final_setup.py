#!/usr/bin/env python3

import cv2
import numpy as np
import serial  # For serial communication
import time
from picamera2 import Picamera2
from ultralytics import YOLO
from datetime import datetime
import os
import json
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter # <-- NEW IMPORT

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
MODEL_PATH = "/home/group4PI/Documents/final_best.pt"
SAVE_DIR = "/home/group4PI/Documents/eggs" 
LOG_PATH = os.path.join(SAVE_DIR, "egg_results.json") 

SIZE_SMALL_MAX = 300  # Max diagonal pixels for "Small/Peewee"
SIZE_MEDIUM_MAX = 375 # Max diagonal pixels for "Medium"

EGG_SETTLE_DELAY_SEC = 1.3   # (1.3s) Time to wait for the egg to stop bouncing
CAPTURE_COOLDOWN_SEC = 2.0   # (2.0s) Time to ignore new triggers after a capture

print(f"Loading model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print("✅ Model loaded.")

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(camera_config)
picam2.start()
print("✅ Camera started.")
time.sleep(2.0) # Allow camera to warm up

os.makedirs(SAVE_DIR, exist_ok=True)
if not os.path.exists(LOG_PATH):
    with open(LOG_PATH, "w") as f:
        json.dump([], f)

def save_result_to_json(result_data):
    try:
        with open(LOG_PATH, "r") as f: data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): data = []
    data.append(result_data)
    with open(LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_egg_size(cropped_image):
    try:
        h, w, _ = cropped_image.shape
        diagonal = np.sqrt(w**2 + h**2)

        if diagonal <= SIZE_SMALL_MAX:
            size_label = "Smal" # Note: Kept as "Smal" from original code
        elif diagonal <= SIZE_MEDIUM_MAX:
            size_label = "Medium"
        else:
            size_label = "Large"
        
        return size_label, round(diagonal, 2)
    except Exception as e:
        print(f"[ERROR] Could not calculate size: {e}")
        return "Unknown", 0.0

def get_stats_from_json():
    try:
        with open(LOG_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    if not data:
        return {
            "total_all_time": 0, 
            "total_today": 0, 
            "label_counts_all_time": Counter(), 
            "label_counts_today": Counter()
        }

    total_all_time = len(data)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    labels_all_time = []
    labels_today = []
    total_today = 0
    
    for entry in data:
        label = entry.get("label", "Unknown")
        labels_all_time.append(label)
        
        if entry.get("timestamp", "").startswith(today_str):
            total_today += 1
            labels_today.append(label)
            
    label_counts_all_time = Counter(labels_all_time)
    label_counts_today = Counter(labels_today)
    
    return {
        "total_all_time": total_all_time,
        "total_today": total_today,
        "label_counts_all_time": label_counts_all_time,
        "label_counts_today": label_counts_today
    }

def main():
    ser = None
    try:
        print(f"Attempting to connect to {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print("✅ Serial connection successful! Starting monitoring UI...")

        captured_img_thumb = np.zeros((120, 160, 3), dtype=np.uint8) # Default black thumbnail
        
        last_result = {
            "label": "N/A", 
            "confidence": 0.0, 
            "size": "N/A",
            "date": "N/A",
            "time": "N/A"
        }
        
        last_capture_time = 0.0 # Variable to track cooldown

        window_name = "Candled Egg Quality Detection"
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        print("Loading initial statistics...")
        stats = get_stats_from_json()
        print(f"✅ Initial stats: {stats}")
      
        LABEL_MAP = {
            "AA - Premium": "AA Premium",
            "A - Good": "A Good",
            "B - Fair": "B Fair", # Updated from "B Fail"
            "Inedible": "Inedible"
        }

        while True:
            frame_rgb = picam2.capture_array()
            display_frame_rgb = frame_rgb.copy()

            if ser.in_waiting > 0:
                message = ser.readline().decode('utf-8').strip()

                if message == "OBJECT_DETECTED":
                    current_time = time.time()
                    
                    if (current_time - last_capture_time) > CAPTURE_COOLDOWN_SEC:
                        
                        last_capture_time = current_time 
                        
                        print(f"\n✨ Trigger received! Waiting {EGG_SETTLE_DELAY_SEC}s for egg to settle...")
                        time.sleep(EGG_SETTLE_DELAY_SEC)
                        
                        ser.reset_input_buffer() 
                        
                        print("Capturing and analyzing settled frame...")
                        analysis_frame = picam2.capture_array() 
                        display_frame_rgb = analysis_frame.copy() 

                        results = model(analysis_frame, verbose=False, conf=0.3)
                        
                        if len(results[0].boxes) > 0:
                            box = results[0].boxes[0]
                            label = model.names[int(box.cls[0])] # This is the grade (e.g., "AA", "A", "B", "Inedible")
                            print(f"!!!!!!!!!! DEBUG: Model label is: '{label}' !!!!!!!!!!")
                            conf = float(box.conf[0])
                            x1, y1, x2, y2 = map(int, box.xyxy[0])

                            text = f"{label} {conf:.2f}"
                            cv2.rectangle(display_frame_rgb, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(display_frame_rgb, text, (x1, y1 - 5), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 0, 0), 2)
                            
                            cropped_egg_rgb = analysis_frame[y1:y2, x1:x2]

                            if cropped_egg_rgb.size > 0:
                                print(f"[INFO] Egg detected: {label} ({conf:.2f})")
                                
                                size_label, diagonal_pixels = get_egg_size(cropped_egg_rgb)
                                print(f"[INFO] Size detected: {size_label} (Diagonal: {diagonal_pixels}px)")

                                serial_command_to_esp32 = f"GRADE_{label}\n"
                                try:
                                    ser.write(serial_command_to_esp32.encode('utf-8'))
                                    print(f"✅ [SERIAL] Sent grade to ESP32: {serial_command_to_esp32.strip()}")
                                except serial.SerialException as e:
                                    print(f"❌ [SERIAL ERROR] Failed to send command: {e}")

                                now = datetime.now()
                                timestamp_str = now.strftime("%Y%m%d_%H%M%S")
                                
                                filename = f"{timestamp_str}_{label}_{size_label}.jpg"
                                filepath = os.path.join(SAVE_DIR, filename)
                                
                                cv2.imwrite(filepath, cropped_egg_rgb)
                                print(f"✅ Cropped egg image saved to {filepath}")

                                result_entry = { 
                                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                                    "label": label, 
                                    "confidence": round(conf, 2), 
                                    "size": size_label,
                                    "diagonal_pixels": diagonal_pixels,
                                    "image_path": filepath 
                                }
                                save_result_to_json(result_entry)

                                stats = get_stats_from_json()
                              
                                last_result = { 
                                    "label": label, 
                                    "confidence": conf, 
                                    "size": size_label,
                                    "date": now.strftime("%m-%d-%Y"),
                                    "time": now.strftime("%I:%M:%S %p")
                                }
                                captured_img_thumb = cv2.resize(cropped_egg_rgb, (160, 120))
                            else:
                                print("[WARN] Detection resulted in an invalid crop.")
                        else:
                            print("[WARN] Trigger received, but no egg detected in settled frame.")
                    
                    else:
                        print(f"\n[INFO] Ignoring duplicate trigger (egg bounce).") 

            panel_width = 320
            
            ui = np.ones((480, panel_width, 3), dtype=np.uint8) * 255 
            
            FONT = cv2.FONT_HERSHEY_DUPLEX
            TH_TEXT = 1
            TH_HEADER = 2
            
            COLOR_BLACK = (0, 0, 0)
            COLOR_BLUE = (255, 0, 0)
            
            header_text = "LAST EGG CAPTURED"
            (w, h), _ = cv2.getTextSize(header_text, FONT, 0.7, TH_HEADER)
            cv2.putText(ui, header_text, ((panel_width - w) // 2, 30), FONT, 0.7, COLOR_BLUE, TH_HEADER)
            
            base_y = 65
            label_x = 20  # X pos for left-aligned labels
            value_x = 90  # X pos for left-aligned values
            
            cv2.putText(ui, "Grade:", (label_x, base_y), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            cv2.putText(ui, last_result['label'], (value_x, base_y), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            
            cv2.putText(ui, "Size:", (label_x, base_y + 30), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            cv2.putText(ui, last_result['size'], (value_x, base_y + 30), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            
            cv2.putText(ui, "Date:", (label_x, base_y + 60), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            cv2.putText(ui, last_result['date'], (value_x, base_y + 60), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            
            cv2.putText(ui, "Time:", (label_x, base_y + 90), FONT, 0.6, COLOR_BLACK, TH_TEXT)
            cv2.putText(ui, last_result['time'], (value_x, base_y + 90), FONT, 0.6, COLOR_BLACK, TH_TEXT)

            thumb_h, thumb_w = 120, 160
            thumb_y_start = 165 # Placed below the text
            try: 
                ui[thumb_y_start:thumb_y_start+thumb_h, (panel_width - thumb_w) // 2 : (panel_width - thumb_w) // 2 + thumb_w] = captured_img_thumb
            except Exception as e: 
                cv2.rectangle(ui, ((panel_width - thumb_w) // 2, thumb_y_start), ((panel_width + thumb_w) // 2, thumb_y_start + thumb_h), COLOR_BLACK, 1)

            stats_y_start = 320 # Pushed way down
            
            header_text_stats = "STATISTICS"
            (w, h), _ = cv2.getTextSize(header_text_stats, FONT, 0.6, TH_HEADER)
            cv2.putText(ui, header_text_stats, ((panel_width - w) // 2, stats_y_start), FONT, 0.6, COLOR_BLUE, TH_HEADER) # Center "STATISTICS"
            
            col_label_x = 20
            col_today_x = 200
            col_all_time_x = 280
            header_text_today = "Today"
            header_text_all = "All Time"
            header_y = stats_y_start + 25 # Move column headers down
            
            (w, h), _ = cv2.getTextSize(header_text_today, FONT, 0.5, TH_TEXT) # Smaller font
            cv2.putText(ui, header_text_today, (col_today_x - (w//2), header_y), FONT, 0.5, COLOR_BLACK, TH_TEXT) # Center "Today"
            
            (w, h), _ = cv2.getTextSize(header_text_all, FONT, 0.5, TH_TEXT) # Smaller font
            cv2.putText(ui, header_text_all, (col_all_time_x - (w//2), header_y), FONT, 0.5, COLOR_BLACK, TH_TEXT) # Center "All Time"
            
            stats_today = stats['label_counts_today']
            stats_all_time = stats['label_counts_all_time']
            
            labels_to_display = ["AA - Premium", "A - Good", "B - Fair", "Inedible"]
            # -------------------------------------------------------
            
            current_y = header_y + 22 # Start rows below the column headers
            
            for label in labels_to_display:
                display_name = LABEL_MAP.get(label, label) + ":"
                today_count = str(stats_today.get(label, 0))
                all_time_count = str(stats_all_time.get(label, 0))
                
                cv2.putText(ui, display_name, (col_label_x, current_y), FONT, 0.5, COLOR_BLACK, TH_TEXT)
                
                (w, h), _ = cv2.getTextSize(today_count, FONT, 0.5, TH_TEXT)
                cv2.putText(ui, today_count, (col_today_x - (w//2), current_y), FONT, 0.5, COLOR_BLACK, TH_TEXT)
                
                (w, h), _ = cv2.getTextSize(all_time_count, FONT, 0.5, TH_TEXT)
                cv2.putText(ui, all_time_count, (col_all_time_x - (w//2), current_y), FONT, 0.5, COLOR_BLACK, TH_TEXT)
                
                current_y += 22 # Move to next row (smaller gap)
            
            current_y += 3 # Add padding before line
            cv2.line(ui, (col_label_x, current_y), (col_all_time_x + 30, current_y), COLOR_BLACK, 1) # Separator line
            current_y += 18 # Add padding after line
            
            total_today_str = str(stats['total_today'])
            total_all_time_str = str(stats['total_all_time'])
            
            cv2.putText(ui, "Total:", (col_label_x, current_y), FONT, 0.55, COLOR_BLACK, TH_HEADER) # Bold Total
            
            (w, h), _ = cv2.getTextSize(total_today_str, FONT, 0.55, TH_HEADER)
            cv2.putText(ui, total_today_str, (col_today_x - (w//2), current_y), FONT, 0.55, COLOR_BLACK, TH_HEADER)
            
            (w, h), _ = cv2.getTextSize(total_all_time_str, FONT, 0.55, TH_HEADER)
            cv2.putText(ui, total_all_time_str, (col_all_time_x - (w//2), current_y), FONT, 0.55, COLOR_BLACK, TH_HEADER)

            combined_view_rgb = np.hstack((display_frame_rgb, ui))
            
            cv2.imshow(window_name, combined_view_rgb)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("'q' pressed. Exiting...")
                break

            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"❌ SERIAL ERROR: Could not open port {SERIAL_PORT}. Details: {e}")
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        print("Closing resources...")
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        picam2.stop()
        cv2.destroyAllWindows()
        print("Program finished.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all devices
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/eggs")
def get_eggs():
    if not os.path.exists(LOG_PATH):
        return {"eggs": []}
    
    try:
        with open(LOG_PATH, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = [] # Return empty list if file is empty

    if isinstance(data, list):
        return {"eggs": data}   
    elif isinstance(data, dict) and "eggs" in data:
        return data
    else:
        return {"eggs": [data]}

app.mount("/images", StaticFiles(directory=SAVE_DIR), name="images")

@app.get("/")
def root():
    return {"message": "Egg API is running! Visit /eggs to view data."}

if __name__ == '__main__':
    
    def run_server():
        print("Starting FastAPI server in background thread...")
        uvicorn.run(app, host="0.0.0.0", port=8000)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("Starting main CV loop in main thread...")
    main()
