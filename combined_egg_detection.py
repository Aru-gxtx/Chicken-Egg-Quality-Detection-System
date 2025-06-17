from picamera2 import Picamera2
import tensorflow as tf
import cv2
import numpy as np
import time

def classify_egg_size(area):
    if area < 2000:
        return "Small"
    elif area < 4000:
        return "Medium"
    else:
        return "Large"

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image

def main():
    # Load quality classification model
    model = tf.keras.models.load_model('egg_quality_model.keras')

    # Initialize camera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "RGB888"})
    picam2.configure(config)
    picam2.set_controls({"AwbEnable": True})
    picam2.start()
    time.sleep(2)  # Give time for camera to warm up

    print("Press SPACE to capture and classify egg quality. Press ESC to exit.")

    while True:
        # Capture frame
        frame = picam2.capture_array()
        
        # Create copies for different processing
        size_frame = frame.copy()
        quality_frame = frame.copy()

        # Size Detection Processing
        gray = cv2.cvtColor(size_frame, cv2.COLOR_BGR2GRAY)
        contrast = cv2.convertScaleAbs(gray, alpha=2, beta=0)
        light_blur = cv2.GaussianBlur(contrast, (3, 3), 0.8)
        edges = cv2.Canny(light_blur, 70, 170)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours for size detection
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:  # Minimum area to reduce noise
                x, y, w, h = cv2.boundingRect(cnt)
                size_class = classify_egg_size(area)
                
                # Draw rectangle and put text for size
                cv2.rectangle(size_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"{size_class} ({int(area)} px)"
                cv2.putText(size_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

        # Display size detection results
        cv2.imshow("Egg Size Detection", size_frame)
        cv2.imshow("Edges", cleaned)

        # Display quality detection window
        cv2.imshow("Egg Quality Detection", quality_frame)

        key = cv2.waitKey(1)
        if key % 256 == 32:  # SPACE key
            # Quality classification
            processed_image = preprocess_image(quality_frame)
            prediction = model.predict(processed_image)[0][0]

            if prediction > 0.5:
                result = "Good Egg"
                color = (0, 255, 0)
            else:
                result = "Bad Egg"
                color = (0, 0, 255)

            result_frame = quality_frame.copy()
            cv2.putText(result_frame, f"{result} ({prediction:.2f})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.imshow("Classification Result", result_frame)
            cv2.waitKey(1500)  # Show for 1.5 seconds

        elif key % 256 == 27:  # ESC key
            break

    # Cleanup
    cv2.destroyAllWindows()
    picam2.close()

if __name__ == "__main__":
    main() 