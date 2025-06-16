import tensorflow as tf
import cv2
import numpy as np

def preprocess_image(image):
    # 1. Resize to match model's expected input
    image = cv2.resize(image, (224, 224))
    
    # 2. Convert BGR to RGB (OpenCV uses BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 3. Normalize pixel values
    image = image / 255.0
    
    # 4. Add batch dimension
    image = np.expand_dims(image, axis=0)
    return image

def main():
    # Load trained model
    model = tf.keras.models.load_model('egg_quality_model.keras')
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    print("Press SPACE to capture and classify an egg. Press ESC to exit.")
    
    while True:
        # Get camera frame
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break
        
        # Show live feed
        cv2.imshow('Egg Quality Detection', frame)
        
        # Wait for key press
        key = cv2.waitKey(1)
        if key % 256 == 32:  # SPACE key
            # 1. Preprocess the image
            processed_image = preprocess_image(frame)
            
            # 2. Get prediction (0-1 value)
            prediction = model.predict(processed_image)[0][0]
            
            # 3. Classify based on threshold
            if prediction > 0.5:
                result = "Good Egg"
                color = (0, 255, 0)  # Green
            else:
                result = "Bad Egg"
                color = (0, 0, 255)  # Red
            
            # 4. Show result
            result_frame = frame.copy()
            cv2.putText(result_frame, f"{result} ({prediction:.2f})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.imshow('Classification Result', result_frame)
            cv2.waitKey(1500)  # Show result for 1.5 seconds
            
        elif key % 256 == 27:  # ESC key
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()