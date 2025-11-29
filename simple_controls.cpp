#include <Arduino.h>
#include <ESP32Servo.h>

const int SORTING_SERVO_PIN = 21; 

Servo sortingServo;

void setup() {
  Serial.begin(115200);
  delay(1000);

  sortingServo.attach(SORTING_SERVO_PIN);
  
  sortingServo.write(0); 
  
  Serial.println("\n--- Servo Angle Tester ---");
  Serial.println("Ready to receive angles (0-180).");
  Serial.print("Servo attached to pin: ");
  Serial.println(SORTING_SERVO_PIN);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    int angle = command.toInt();

    if (command.length() > 0) {
      if (angle >= 0 && angle <= 180) {
        Serial.print("Received angle: ");
        Serial.print(angle);
        Serial.println(" -> Moving servo.");
        sortingServo.write(angle);
      } else {
        Serial.print("Invalid angle. Must be 0-180. Received: ");
        Serial.println(command);
      }
    }
  }
  
  delay(50);
}
