from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

# Load trained YOLOv8 model
MODEL_PATH = "C:/Users/admin/Downloads/runs/content/runs/detect/train/weights/best.pt"
model = YOLO(MODEL_PATH)

# Size classification based on bounding box area
def classify_egg_size(area):
    if area < 2000:
        return "Small"
    elif area < 4000:
        return "Medium"
    else:
        return "Large"

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Store last detected egg info and crop
last_result = {
    "label": "N/A",
    "size": "N/A",
    "confidence": 0.0,
    "time": "N/A"
}
last_crop = np.zeros((200, 200, 3), dtype=np.uint8)  # placeholder black image

print("Candled Egg Quality Detection Started")
print("-" * 50)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    h, w = frame.shape[:2]
    # Define center region (middle 40% of width and height)
    cx_min, cx_max = int(w * 0.3), int(w * 0.7)
    cy_min, cy_max = int(h * 0.3), int(h * 0.7)

    # Run YOLOv8 detection
    results = model(frame, verbose=False)

    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = model.names[cls_id]

            # Area & size
            area = (x2 - x1) * (y2 - y1)
            size_class = classify_egg_size(area)

            # Draw box on video
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Center of detected box
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # Only capture if egg is in the middle region
            if cx_min < cx < cx_max and cy_min < cy < cy_max:
                # Update last result
                last_result = {
                    "label": label,
                    "size": size_class,
                    "confidence": conf,
                    "time": datetime.now().strftime("%H:%M:%S")
                }
                # Save cropped egg (with padding)
                pad = 15
                x1c, y1c = max(x1 - pad, 0), max(y1 - pad, 0)
                x2c, y2c = min(x2 + pad, w), min(y2 + pad, h)
                crop = frame[y1c:y2c, x1c:x2c]
                if crop.size > 0:
                    last_crop = cv2.resize(crop, (200, 200))

    # ---------------------------
    # Create side UI panel
    # ---------------------------
    panel_width = 320
    panel_height = frame.shape[0]
    panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)

    # Title
    cv2.putText(panel, "Egg Detection Info", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Show cropped last egg
    crop_y = 80
    panel[crop_y:crop_y+200, 60:260] = last_crop

    # Show details below
    base_y = crop_y + 230
    cv2.putText(panel, f"Grade: {last_result['label']}", (20, base_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(panel, f"Size: {last_result['size']}", (20, base_y+40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(panel, f"Conf: {last_result['confidence']:.2f}", (20, base_y+80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(panel, f"Time: {last_result['time']}", (20, base_y+120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Merge video feed + panel
    combined = np.hstack((frame, panel))

    cv2.imshow("Candled Egg Quality Detection", combined)

    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
