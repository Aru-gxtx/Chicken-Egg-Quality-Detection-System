import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os

# Create directories if they don't exist
os.makedirs('dataset/good', exist_ok=True)
os.makedirs('dataset/bad', exist_ok=True)

# Set up data generators with augmentation
datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values
    validation_split=0.2,  # 20% for validation
    rotation_range=20,  # Random rotation
    width_shift_range=0.2,  # Random horizontal shift
    height_shift_range=0.2,  # Random vertical shift
    horizontal_flip=True,  # Random horizontal flip
    fill_mode='nearest'  # Fill mode for transformations
)

# Load and preprocess the training data
train_generator = datagen.flow_from_directory(
    'dataset',
    target_size=(224, 224),  # Resize images to 224x224
    batch_size=32,
    class_mode='binary',  # Binary classification (good/bad)
    subset='training'
)

# Load and preprocess the validation data
validation_generator = datagen.flow_from_directory(
    'dataset',
    target_size=(224, 224),
    batch_size=32,
    class_mode='binary',
    subset='validation'
)

# Print class indices
print("\nClass indices:", train_generator.class_indices)

# Build a simple CNN model
model = tf.keras.Sequential([
    # First Convolutional Block
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    
    # Second Convolutional Block
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    
    # Third Convolutional Block
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    
    # Flatten and Dense Layers
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.5),  # Add dropout to prevent overfitting
    tf.keras.layers.Dense(1, activation='sigmoid')  # Output layer for binary classification
])

# Compile the model
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Print model summary
model.summary()

# Train the model
print("\nTraining the model...")
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=20,  # Number of training epochs
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
    ]
)

# Save the trained model
model.save('egg_quality_model.keras')
print("\nModel saved as 'egg_quality_model.keras'")

# Print training results
print("\nTraining Results:")
print(f"Final Training Accuracy: {history.history['accuracy'][-1]:.4f}")
print(f"Final Validation Accuracy: {history.history['val_accuracy'][-1]:.4f}")