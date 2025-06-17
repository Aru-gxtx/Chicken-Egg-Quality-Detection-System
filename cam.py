from picamera2 import Picamera2
import cv2
import numpy as np
import time

def classify_egg(area):
    if area < 2000:
        return "Small"
    elif area < 4000:
        return "Medium"
    else:
        return "Large"

# Initialize camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888"})
picam2.configure(config)
picam2.set_controls({"AwbEnable": True})
picam2.start()
time.sleep(2)

while True:
    frame = picam2.capture_array()

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Improve contrast
    contrast = cv2.convertScaleAbs(gray, alpha=2, beta=0)

    # Slight Gaussian blur to stabilize edge detection
    light_blur = cv2.GaussianBlur(contrast, (3, 3), 0.8)

    # Canny edge detection
    edges = cv2.Canny(light_blur, 70, 170)

    # Clean up edges with light morphological closing
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1000:  # Minimum area to reduce noise
            x, y, w, h = cv2.boundingRect(cnt)
            size_class = classify_egg(area)

            # Draw rectangle and put text
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"{size_class} ({int(area)} px)"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

    # Display the result
    cv2.imshow("Egg Size Detection", frame)
    cv2.imshow("Edges", cleaned)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
