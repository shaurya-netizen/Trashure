#include <Wire.h>
#include <MPU6050.h>

// ==========================
// PIN CONFIG
// ==========================
#define MPU_SDA 21
#define MPU_SCL 22
#define TRIG_PIN 5
#define ECHO_PIN 18
#define CAM_TX 17   // ESP32 TX -> ESP32-CAM RX

// ==========================
// OBJECTS
// ==========================
MPU6050 mpu;

// ==========================
// VARIABLES
// ==========================
int16_t ax, ay, az;
float angleX = 0, prevAngleX = 0;

// ==========================
// LID THRESHOLDS
// ==========================
float OPEN_THRESHOLD = 8.0;     // Lid open if angle > 8
float CLOSED_THRESHOLD = 5.0;   // Lid closed if angle < 5

// ==========================
// STABILITY SETTINGS
// ==========================
float STABLE_DELTA = 1.5;               // Stable if angle changes little
unsigned long STABLE_TIME_REQUIRED = 2000; // 2 sec stable before capture
unsigned long CAPTURE_DELAY = 500;
unsigned long COOLDOWN_TIME = 5000;     // Prevent duplicate triggers

// ==========================
// BIN SETTINGS
// ==========================
String BIN_ID = "BIN-01";

// ==========================
// ULTRASONIC CALIBRATION
// ==========================
// CHANGE THESE BASED ON YOUR BIN
float EMPTY_DISTANCE = 18.0;  // distance when bin empty
float FULL_DISTANCE = 5.0;    // distance when bin full

// ==========================
// STATE MACHINE
// ==========================
enum LidState {
  WAIT_FOR_OPEN,
  WAIT_FOR_CLOSE_STABLE
};

LidState state = WAIT_FOR_OPEN;

// ==========================
// TRACKING
// ==========================
bool lidOpened = false;
unsigned long stableStart = 0;
unsigned long lastTriggerTime = 0;
float lastStableAngle = 0;

// ==========================
// FUNCTIONS
// ==========================
float getRawAngle() {
  mpu.getAcceleration(&ax, &ay, &az);
  return atan2(ay, az) * 180 / PI;
}

float getAngle() {
  float raw = getRawAngle();

  // smoothing
  angleX = 0.7 * prevAngleX + 0.3 * raw;
  prevAngleX = angleX;

  return angleX;
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return EMPTY_DISTANCE;
  }

  return duration * 0.034 / 2;
}

int getFill(float d) {
  int fill = map((int)(d * 10), (int)(EMPTY_DISTANCE * 10), (int)(FULL_DISTANCE * 10), 0, 100);
  return constrain(fill, 0, 100);
}

void sendCapture(int fill) {
  String message = "CAPTURE|" + BIN_ID + "|" + String(fill);
  Serial2.println(message);

  Serial.println("📤 Sent to ESP32-CAM:");
  Serial.println(message);
}

// ==========================
// SETUP
// ==========================
void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, -1, CAM_TX);

  Wire.begin(MPU_SDA, MPU_SCL);
  mpu.initialize();

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.println("🚀 ESP32 BIN CONTROLLER READY");
  delay(2000);
}

// ==========================
// LOOP
// ==========================
void loop() {
  float angle = getAngle();

  Serial.print("Angle: ");
  Serial.println(angle);

  switch (state) {

    // ==========================
    // WAIT FOR OPEN
    // ==========================
    case WAIT_FOR_OPEN:
      if (angle > OPEN_THRESHOLD && millis() - lastTriggerTime > COOLDOWN_TIME) {
        Serial.println("🟢 Lid OPEN detected");
        lidOpened = true;
        state = WAIT_FOR_CLOSE_STABLE;
        stableStart = millis();
        lastStableAngle = angle;
      }
      break;

    // ==========================
    // WAIT FOR CLOSE + STABLE
    // ==========================
    case WAIT_FOR_CLOSE_STABLE:
      if (lidOpened && angle < CLOSED_THRESHOLD) {
        Serial.println("🔵 Lid CLOSED detected");

        if (abs(angle - lastStableAngle) <= STABLE_DELTA) {
          if (millis() - stableStart >= STABLE_TIME_REQUIRED) {
            Serial.println("✅ Lid is stable. Capturing...");

            delay(CAPTURE_DELAY);

            float distance = getDistance();
            int fill = getFill(distance);

            Serial.print("📏 Distance: ");
            Serial.print(distance);
            Serial.println(" cm");

            Serial.print("🗑️ Fill Level: ");
            Serial.print(fill);
            Serial.println("%");

            sendCapture(fill);

            lidOpened = false;
            state = WAIT_FOR_OPEN;
            lastTriggerTime = millis();
          }
        } else {
          stableStart = millis();
          lastStableAngle = angle;
        }
      }
      else if (angle > OPEN_THRESHOLD) {
        // Lid still open / moving
        stableStart = millis();
        lastStableAngle = angle;
      }
      break;
  }

  delay(200);
}