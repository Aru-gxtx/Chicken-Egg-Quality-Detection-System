import tensorflow as tf
import cv2
import numpy as np
import time
from datetime import datetime
from pathlib import Path
import sys
import json

BASE_DIR = Path(__file__).resolve().parent

# Force use of the 4-class model only; fail fast if missing
MODEL_PATH = BASE_DIR / "egg_quality_4class_model.keras"
if not MODEL_PATH.exists():
    print(f"Error: 4-class model not found at '{MODEL_PATH}'. Place egg_quality_4class_model.keras next to this script.")
    sys.exit(1)

print(f"Loading 4-class model from: {MODEL_PATH}")
model = tf.keras.models.load_model(str(MODEL_PATH))

# load class mapping (expects JSON like {"A_Good":0,"B_Fair":1,...})
MAPPING_PATH = BASE_DIR / "class_mapping.json"
if not MAPPING_PATH.exists():
    print(f"Error: class mapping file not found at '{MAPPING_PATH}'.")
    print("Create 'class_mapping.json' next to this script with contents like: {\"A_Good\":0, \"B_Fair\":1, \"AA_Premium\":2, \"C_Poor\":3}")
    sys.exit(1)

with open(MAPPING_PATH, "r", encoding="utf-8") as f:
    class_mapping = json.load(f)

# build index -> label map (handles values that are ints or strings)
index_to_label = {int(v): k for k, v in class_mapping.items()}

def classify_egg_size(area):
    if area < 2000:
        return "Small"
    elif area < 4000:
        return "Medium"
    else:
        return "Large"

def is_egg_shape(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if area < 500:
        return False
    circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w)/h
    return 0.4 <= circularity <= 0.95 and 0.5 <= aspect_ratio <= 1.8

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image

def simulate_candling(frame):
    height, width = frame.shape[:2]
    candled = frame.copy()
    candled[height//2:] = cv2.add(candled[height//2:], 50)
    return candled

def resize_for_display(img, scale=0.75):
    h, w = img.shape[:2]
    return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

def crop_contour_region(frame, contour, pad_frac=0.25):
    x, y, w, h = cv2.boundingRect(contour)
    pad = int(max(w, h) * pad_frac)
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, frame.shape[1])
    y1 = min(y + h + pad, frame.shape[0])
    return frame[y0:y1, x0:x1], (x0, y0, x1, y1)

def main():
    # Use laptop webcam instead of Picamera2
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW often stabilizes on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        print("Error: Could not open laptop camera (VideoCapture(0)).")
        return

    time.sleep(1.0)  # camera warm-up
    print("Egg Detection System Started (webcam)")
    print("Waiting for eggs...")
    print("-" * 50)
    detection_start_time = None
    current_egg_data = {
        "size": None,
        "quality": None,
        "timestamp": None,
        "quality_image": None
    }
    detection_in_progress = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # skip a single failed capture, continue loop
                time.sleep(0.05)
                continue

            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            contrast = cv2.convertScaleAbs(gray, alpha=2, beta=0)
            light_blur = cv2.GaussianBlur(contrast, (5, 5), 0.8)
            edges = cv2.Canny(light_blur, 50, 150)
            kernel = np.ones((3, 3), np.uint8)
            cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_contour = None
            max_area = 0
            for cnt in contours:
                if is_egg_shape(cnt):
                    area = cv2.contourArea(cnt)
                    if area > max_area:
                        max_area = area
                        best_contour = cnt

            egg_detected = best_contour is not None

            if egg_detected:
                (cx, cy), radius = cv2.minEnclosingCircle(best_contour)
                center = (int(cx), int(cy))
                radius = int(radius)
                cv2.circle(display_frame, center, radius, (0, 255, 0), 2)

                size_class = classify_egg_size(max_area)
                if len(best_contour) >= 5:
                    ellipse = cv2.fitEllipse(best_contour)
                    cv2.ellipse(display_frame, ellipse, (0, 255, 0), 2)
                    (center_e, axes, angle) = ellipse
                    label_pos = (int(center_e[0] - axes[0] / 2), int(center_e[1] - axes[1] / 2) - 10)
                else:
                    x, y, w, h = cv2.boundingRect(best_contour)
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label_pos = (x, y - 10)

                label = f"{size_class} ({int(max_area)} px)"
                cv2.putText(display_frame, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                crop, crop_rect = crop_contour_region(frame, best_contour, pad_frac=0.25)

                if not detection_in_progress:
                    detection_start_time = time.time()
                    detection_in_progress = True
                    current_egg_data["size"] = size_class
                    current_egg_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    current_egg_data["quality"] = None

            if detection_in_progress and egg_detected:
                elapsed_time = time.time() - detection_start_time
                if elapsed_time >= 1.0 and current_egg_data["quality"] is None:
                    candled_crop = simulate_candling(crop)
                    processed_image = preprocess_image(candled_crop)

                    # 4-class prediction: get class probabilities, pick argmax, map to label
                    preds = model.predict(processed_image, verbose=0)[0]   # e.g. [0.1,0.7,0.15,0.05]
                    idx = int(np.argmax(preds))
                    conf = float(preds[idx])
                    label = index_to_label.get(idx, f"class_{idx}")

                    current_egg_data["quality"] = label
                    result_frame = candled_crop.copy()

                    # choose color mapping as appropriate for your labels; adjust below if needed
                    good_labels = {"A_Good", "AA_Premium"}   # set the labels you consider "good"
                    color = (0, 255, 0) if label in good_labels else (0, 0, 255)

                    cv2.putText(result_frame, f"{label} ({conf:.2f})",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    current_egg_data["quality_image"] = resize_for_display(result_frame, scale=0.75)
                    print(f"\nEgg Detected at {current_egg_data['timestamp']}")
                    print(f"Size: {current_egg_data['size']}")
                    print(f"Quality: {current_egg_data['quality']} (Confidence: {conf:.2f})")
                    print("-" * 50)
                    detection_in_progress = False
            elif detection_in_progress and not egg_detected:
                detection_in_progress = False
                current_egg_data = {"size": None, "quality": None, "timestamp": None, "quality_image": None}

            display_frame_big = resize_for_display(display_frame, scale=0.75)
            cleaned_big = resize_for_display(cleaned, scale=0.75)
            cv2.imshow("Egg Detection System", display_frame_big)
            cv2.imshow("Edge Detection", cleaned_big)
            if current_egg_data["quality_image"] is not None:
                cv2.imshow("Quality Classification", current_egg_data["quality_image"])
                cv2.waitKey(1500)
                current_egg_data["quality_image"] = None
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()