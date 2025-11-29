import cv2
from picamera2 import Picamera2
import time

picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(preview_config)
picam2.start()
time.sleep(1) # Allow camera to start

print("Showing OpenCV preview. Press 'q' to quit.")
while True:
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) 
    cv2.imshow("Camera Preview", frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
picam2.stop()
print("Preview stopped.")
