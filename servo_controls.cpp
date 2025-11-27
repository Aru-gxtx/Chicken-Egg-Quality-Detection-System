#include <Arduino.h>
#include <ESP32Servo.h>

const int PUSHER_SERVO_PIN = 18;
const int SORTING_SERVO_PIN = 21; // <-- NEW: Pin for the sorting servo
const int IR_SENSOR_PIN = 19;

const int PUSHER_PUSH_ANGLE = 0;
const int PUSHER_IDLE_ANGLE = 90;

const int SORTING_IDLE_ANGLE = 0; // Waiting position
const int SORTING_AA_ANGLE = 63;
const int SORTING_A_ANGLE = 43;
const int SORTING_B_ANGLE = 20;
const int SORTING_INEDIBLE_ANGLE = 0;

Servo pusherServo;
Servo sortingServo; // <-- NEW

TaskHandle_t irTaskHandle = NULL;
TaskHandle_t pusherTaskHandle = NULL;
TaskHandle_t serialTaskHandle = NULL; // <-- NEW

void irSensorTask(void *pvParameters) {
  Serial.println("IR Sensor Task started. Ready to send messages to Pi.");
  int lastState = digitalRead(IR_SENSOR_PIN);

  for (;;) {
    int currentState = digitalRead(IR_SENSOR_PIN);

    if (currentState != lastState) {
      if (currentState == LOW) { // Object just appeared
        Serial.println("OBJECT_DETECTED");
      } else { // Object just disappeared
        Serial.println("OBJECT_GONE");
        xTaskNotify(pusherTaskHandle, 0, eSetValueWithOverwrite); // Send 0 for GONE
      }
      lastState = currentState;
    }
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

void pusherMotorTask(void *pvParameters) {
  Serial.println("Pusher Motor Task started");
  uint32_t receivedCommand;

  for (;;) {
    if (xTaskNotifyWait(0x00, ULONG_MAX, &receivedCommand, portMAX_DELAY) == pdPASS) {

      if (receivedCommand == 1) { // Command (1) now comes from serial task
        Serial.println("Pusher task received PUSH command. Waiting 1 second..."); // <-- MODIFICATION
        vTaskDelay(1000 / portTICK_PERIOD_MS); // <-- MODIFICATION: Changed from 1500 to 1000

        Serial.println("Moving pusher servo to PUSH angle.");
        pusherServo.write(PUSHER_PUSH_ANGLE);

      } else if (receivedCommand == 0) { // Object GONE (from IR task)
        Serial.println("Pusher task received GONE command. Waiting 0.2 seconds before retracting."); // <-- MODIFICATION V3
        vTaskDelay(200 / portTICK_PERIOD_MS); // <-- MODIFICATION V3: Added 0.2s delay

        Serial.println("Moving pusher servo to IDLE angle.");
        pusherServo.write(PUSHER_IDLE_ANGLE);
      }
    }
  }
}
void serialMonitorTask(void *pvParameters) {
  Serial.println("Serial Monitor Task started. Listening for grade commands from Pi.");
  String serialCommand; // String to buffer incoming serial data

  for (;;) {
    while (Serial.available() > 0) {
      char c = Serial.read();

      if (c == '\n') { // Command received (end-of-line)
        serialCommand.trim(); // Remove any whitespace
        Serial.print("Received command from Pi: ");
        Serial.println(serialCommand);

        serialCommand.toUpperCase(); // Normalize to uppercase

        bool validCommand = false; // Flag to check if we should notify the pusher

        if (serialCommand.startsWith("GRADE_AA")) {
          sortingServo.write(SORTING_AA_ANGLE);
          validCommand = true;
        } else if (serialCommand.startsWith("GRADE_A")) {
          sortingServo.write(SORTING_A_ANGLE);
          validCommand = true;
        } else if (serialCommand.startsWith("GRADE_B")) {
          sortingServo.write(SORTING_B_ANGLE);
          validCommand = true;
        } else if (serialCommand.startsWith("GRADE_INEDIBLE")) {
          sortingServo.write(SORTING_INEDIBLE_ANGLE);
          validCommand = true;
        } else {
          Serial.print("Unknown command: ");
          Serial.println(serialCommand);
        }

        if (validCommand) {
          Serial.println("Sorting servo moved. Notifying pusher task to begin push sequence.");
          xTaskNotify(pusherTaskHandle, 1, eSetValueWithOverwrite); // Send 1 for PUSH
        }

        serialCommand = ""; // Clear the buffer for the next command
      } else {
        serialCommand += c; // Add character to the buffer
      }
    }
    vTaskDelay(20 / portTICK_PERIOD_MS); // Small delay to prevent CPU hogging
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(IR_SENSOR_PIN, INPUT);

  pusherServo.attach(PUSHER_SERVO_PIN);
  sortingServo.attach(SORTING_SERVO_PIN); // <-- NEW

  pusherServo.write(PUSHER_IDLE_ANGLE);
  sortingServo.write(SORTING_IDLE_ANGLE); // <-- NEW

  Serial.println("Setup complete. Both servos at idle.");

  xTaskCreate(irSensorTask, "IR Sensor Task", 2048, NULL, 1, &irTaskHandle);
  xTaskCreate(pusherMotorTask, "Pusher Motor Task", 2048, NULL, 2, &pusherTaskHandle);
  xTaskCreate(serialMonitorTask, "Serial Monitor Task", 2048, NULL, 1, &serialTaskHandle); // <-- NEW
}

void loop() {
  vTaskDelay(1000 / portTICK_PERIOD_MS);
}
