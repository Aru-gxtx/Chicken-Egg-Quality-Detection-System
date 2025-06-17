from picamera2 import Picamera2
import tensorflow as tf
import cv2
import numpy as np
import time

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image

def main():
    # Load model
    model = tf.keras.models.load_model('egg_quality_model.keras')

    # Initialize Picamera2
    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    time.sleep(2)  # Give time for camera to warm up

    print("Press SPACE to capture and classify an egg. Press ESC to exit.")

    while True:
        # Capture frame from PiCamera2
        frame = picam2.capture_array()

        # Display live camera feed
        cv2.imshow("Egg Quality Detection", frame)

        key = cv2.waitKey(1)
        if key % 256 == 32:  # SPACE key
            # Preprocess and predict
            processed_image = preprocess_image(frame)
            prediction = model.predict(processed_image)[0][0]

            if prediction > 0.5:
                result = "Good Egg"
                color = (0, 255, 0)
            else:
                result = "Bad Egg"
                color = (0, 0, 255)

            result_frame = frame.copy()
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
