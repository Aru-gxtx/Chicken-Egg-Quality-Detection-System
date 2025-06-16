import cv2
import numpy as np

def classify_egg(area):
    if area < 2000:
        return "Small"
    elif area < 4000:
        return "Medium"
    else:
        return "Large"

# Webcam
cap = cv2.VideoCapture(0)

# Detection stability
detected_frames = 0
threshold_frames = 3

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))
    h, w = frame.shape[:2]
    frame = frame[h//4:3*h//4, w//4:3*w//4]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    blurred = cv2.GaussianBlur(inverted, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)

    # Morphological filtering
    kernel = np.ones((5, 5), np.uint8)
    cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    egg_detected = False

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 2000 and len(contour) >= 5:
            ellipse = cv2.fitEllipse(contour)
            major, minor = ellipse[1]
            aspect_ratio = max(major, minor) / min(major, minor)

            # Filter for elliptical/egg-like shapes
            if 1.3 < aspect_ratio < 2.2:
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0

                # Extent = area / bounding rect area
                x, y, w_rect, h_rect = cv2.boundingRect(contour)
                rect_area = w_rect * h_rect
                extent = area / rect_area if rect_area > 0 else 0

                # Circularity = (4π × Area) / Perimeter²
                perimeter = cv2.arcLength(contour, True)
                circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

                # Ellipse area comparison
                ellipse_area = (np.pi * major * minor) / 4
                ellipse_fit_ratio = area / ellipse_area if ellipse_area > 0 else 0

                if 0.85 < solidity < 1.1 and 0.6 < extent < 0.95 and 0.4 < circularity < 0.8 and 0.7 < ellipse_fit_ratio < 1.3:
                    egg_detected = True
                    if detected_frames >= threshold_frames:
                        size = classify_egg(area)
                        cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Size: {size}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        cv2.putText(frame, f"Area: {int(area)} px", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                    break

    if egg_detected:
        detected_frames += 1
    else:
        detected_frames = 0

    cv2.imshow("Live Egg Detection", frame)
    cv2.imshow("Edges", cleaned)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
