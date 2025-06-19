import tensorflow as tf
import cv2
import numpy as np
import time
from datetime import datetime
from picamera2 import Picamera2

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

def create_black_background(frame):
    height, width = frame.shape[:2]
    black_bg = np.zeros((height, width, 3), dtype=np.uint8)
    black_bg[:height//2] = frame[:height//2]
    return black_bg

def simulate_candling(frame):
    height, width = frame.shape[:2]
    candled = frame.copy()
    candled[height//2:] = cv2.add(candled[height//2:], 50)
    return candled

def resize_for_display(img, scale=0.5):
    h, w = img.shape[:2]
    return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

def main():
    model = tf.keras.models.load_model('egg_quality_model.keras')
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "RGB888"})
    picam2.configure(config)
    picam2.set_controls({"AwbEnable": True})
    picam2.start()
    time.sleep(2)
    print("Egg Detection System Started")
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
    while True:
        frame = picam2.capture_array()
        display_frame = create_black_background(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = cv2.convertScaleAbs(gray, alpha=2, beta=0)
        light_blur = cv2.GaussianBlur(contrast, (5, 5), 0.8)
        edges = cv2.Canny(light_blur, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(display_frame, contours, -1, (0, 255, 255), 1)
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
            size_class = classify_egg_size(max_area)
            if len(best_contour) >= 5:
                ellipse = cv2.fitEllipse(best_contour)
                cv2.ellipse(display_frame, ellipse, (0, 255, 0), 2)
                (center, axes, angle) = ellipse
                label_pos = (int(center[0] - axes[0] / 2), int(center[1] - axes[1] / 2) - 10)
            else:
                x, y, w, h = cv2.boundingRect(best_contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label_pos = (x, y - 10)
            label = f"{size_class} ({int(max_area)} px)"
            cv2.putText(display_frame, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)
            if not detection_in_progress:
                detection_start_time = time.time()
                detection_in_progress = True
                current_egg_data["size"] = size_class
                current_egg_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if detection_in_progress and egg_detected:
            elapsed_time = time.time() - detection_start_time
            if elapsed_time >= 2.0 and current_egg_data["quality"] is None:
                candled_frame = simulate_candling(frame)
                processed_image = preprocess_image(candled_frame)
                prediction = model.predict(processed_image)[0][0]
                current_egg_data["quality"] = "Good" if prediction > 0.5 else "Bad"
                result_frame = candled_frame.copy()
                color = (0, 255, 0) if prediction > 0.5 else (0, 0, 255)
                cv2.putText(result_frame, f"{current_egg_data['quality']} (Confidence: {prediction:.2f})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                current_egg_data["quality_image"] = resize_for_display(result_frame, scale=0.5)
                print(f"\nEgg Detected at {current_egg_data['timestamp']}")
                print(f"Size: {current_egg_data['size']}")
                print(f"Quality: {current_egg_data['quality']} (Confidence: {prediction:.2f})")
                print("-" * 50)
                detection_in_progress = False
                current_egg_data = {"size": None, "quality": None, "timestamp": None, "quality_image": current_egg_data["quality_image"]}
        elif detection_in_progress and not egg_detected:
            detection_in_progress = False
            current_egg_data = {"size": None, "quality": None, "timestamp": None, "quality_image": None}
        display_frame_small = resize_for_display(display_frame, scale=0.5)
        cleaned_small = resize_for_display(cleaned, scale=0.5)
        cv2.imshow("Egg Detection System", display_frame_small)
        cv2.imshow("Edge Detection", cleaned_small)
        if current_egg_data["quality_image"] is not None:
            cv2.imshow("Quality Classification", current_egg_data["quality_image"])
            cv2.waitKey(3000)
            current_egg_data["quality_image"] = None
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()