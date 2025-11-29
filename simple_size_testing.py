import cv2
import numpy as np
import time
from picamera2 import Picamera2
from ultralytics import YOLO

MODEL_PATH = "/home/group4PI/Documents/bestfrfr.pt" 

SIZE_SMALL_MAX = 300  # Max diagonal pixels for "Small/Peewee"
SIZE_MEDIUM_MAX = 375 # Max diagonal pixels for "Medium"

print(f"Loading model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print("✅ Model loaded.")

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(camera_config)
picam2.start()
print("✅ Camera started. Warming up...")
time.sleep(2.0)

def get_egg_size(cropped_image):
    try:
        h, w, _ = cropped_image.shape
        diagonal = np.sqrt(w**2 + h**2)

        if diagonal <= SIZE_SMALL_MAX:
            size_label = "Small/Peewee"
        elif diagonal <= SIZE_MEDIUM_MAX:
            size_label = "Medium"
        else:
            size_label = "Large/Jumbo"
        
        return size_label, round(diagonal, 2)
    except Exception as e:
        print(f"[ERROR] Could not calculate size: {e}")
        return "Unknown", 0.0

def main_tuner():
    print("\nStarting Egg Size Tuner...")
    print("Press 'q' in the OpenCV window to quit.")
    
    try:
        while True:
            frame_rgb = picam2.capture_array()
            
            results = model(frame_rgb, verbose=False, conf=0.3)
            
            if len(results[0].boxes) > 0:
                box = results[0].boxes[0]
                label = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                cropped_egg_rgb = frame_rgb[y1:y2, x1:x2]

                if cropped_egg_rgb.size > 0:
                    
                    size_label, diagonal_pixels = get_egg_size(cropped_egg_rgb)

                    cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    text = f"{label} {conf:.2f}"
                    cv2.putText(frame_rgb, text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    diag_text = f"Diagonal: {diagonal_pixels} px"
                    cv2.putText(frame_rgb, diag_text, (x1, y2 + 25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                                
                    size_text = f"Size: {size_label}"
                    cv2.putText(frame_rgb, size_text, (x1, y2 + 55), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.imshow("Egg Size Tuner (Press 'q' to quit)", frame_rgb)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("'q' pressed. Exiting...")
                break
            
            time.sleep(0.01) # Keep it responsive

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        print("Closing resources...")
        picam2.stop()
        cv2.destroyAllWindows()
        print("Tuner finished.")

if __name__ == '__main__':
    main_tuner()
