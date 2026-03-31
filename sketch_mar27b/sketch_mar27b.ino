#include "esp_camera.h"
#include <WiFi.h>

// ==========================
// CAMERA PINS (AI-Thinker ESP32-CAM)
// ==========================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0

#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ==========================
// WIFI
// ==========================
const char* ssid = "canon3000";
const char* password = "Ujjwal@4247ns";

// ==========================
// BACKEND CONFIG
// ==========================
const char* SERVER_IP = "192.168.0.101";
const int SERVER_PORT = 8000;
const char* SERVER_PATH = "/api/process-event";

// ==========================
// HARDWARE
// ==========================
#define FLASH_LED 4

// ==========================
// DATA FROM ESP32
// ==========================
String currentBinId = "BIN-01";
String currentFillLevel = "0";

// ==========================
// CAMERA SETUP
// ==========================
void setupCamera() {
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  // ✅ FIXED (sscb, not sccb)
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn  = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QQVGA;
    config.jpeg_quality = 15;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 1);
    s->set_contrast(s, 1);
    s->set_saturation(s, 0);
    s->set_sharpness(s, 1);
  }

  Serial.println("📷 Camera initialized");
}

// ==========================
// TEST BACKEND CONNECTION
// ==========================
void testServerConnection() {
  WiFiClient testClient;

  Serial.println("🔍 Testing backend connection...");

  if (testClient.connect(SERVER_IP, SERVER_PORT)) {
    Serial.println("✅ Backend reachable!");
    testClient.stop();
  } else {
    Serial.println("❌ Backend NOT reachable");
  }
}

// ==========================
// SEND IMAGE TO BACKEND
// ==========================
void sendImage(camera_fb_t *fb) {
  WiFiClient client;

  String boundary = "----ESP32Boundary";

  String head = "";
  head += "--" + boundary + "\r\n";
  head += "Content-Disposition: form-data; name=\"binId\"\r\n\r\n";
  head += currentBinId + "\r\n";

  head += "--" + boundary + "\r\n";
  head += "Content-Disposition: form-data; name=\"fillLevel\"\r\n\r\n";
  head += currentFillLevel + "\r\n";

  head += "--" + boundary + "\r\n";
  head += "Content-Disposition: form-data; name=\"image\"; filename=\"capture.jpg\"\r\n";
  head += "Content-Type: image/jpeg\r\n\r\n";

  String tail = "\r\n--" + boundary + "--\r\n";

  int totalLen = head.length() + fb->len + tail.length();

  Serial.println("📤 Starting upload...");

  if (!client.connect(SERVER_IP, SERVER_PORT)) {
    Serial.println("❌ Connection failed");
    return;
  }

  client.println("POST " + String(SERVER_PATH) + " HTTP/1.1");
  client.println("Host: " + String(SERVER_IP));
  client.println("Connection: close");
  client.println("Content-Type: multipart/form-data; boundary=" + boundary);
  client.print("Content-Length: ");
  client.println(totalLen);
  client.println();

  client.print(head);
  client.write(fb->buf, fb->len);
  client.print(tail);

  Serial.println("📡 Upload sent, waiting response...");

  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 10000) {
      Serial.println("❌ Server response timeout");
      client.stop();
      return;
    }
  }

  Serial.println("📩 Server response:");
  while (client.available()) {
    String line = client.readStringUntil('\n');
    Serial.println(line);
  }

  Serial.println("✅ Upload complete");
  client.stop();
}

// ==========================
// CAPTURE FRESH IMAGE
// ==========================
void captureAndUpload() {
  Serial.println("⏳ Waiting before capture...");
  delay(1200);

  digitalWrite(FLASH_LED, HIGH);
  delay(400);

  camera_fb_t *fb = NULL;

  // Flush old frames
  Serial.println("🧹 Flushing stale frames...");
  for (int i = 0; i < 2; i++) {
    fb = esp_camera_fb_get();
    if (fb) {
      esp_camera_fb_return(fb);
    }
    delay(200);
  }

  fb = esp_camera_fb_get();

  if (!fb) {
    Serial.println("❌ Fresh capture failed");
    digitalWrite(FLASH_LED, LOW);
    return;
  }

  Serial.println("📸 Fresh image captured");
  Serial.printf("🖼️ Size: %d bytes\n", fb->len);

  sendImage(fb);

  esp_camera_fb_return(fb);
  digitalWrite(FLASH_LED, LOW);
}

// ==========================
// SETUP
// ==========================
void setup() {
  Serial.begin(115200);

  pinMode(FLASH_LED, OUTPUT);
  digitalWrite(FLASH_LED, LOW);

  setupCamera();

  WiFi.begin(ssid, password);
  Serial.print("📶 Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi connected");
  Serial.print("🌐 IP: ");
  Serial.println(WiFi.localIP());

  testServerConnection();

  Serial.println("📡 ESP32-CAM READY");
}

// ==========================
// LOOP
// ==========================
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("CAPTURE|")) {
      int firstSep = cmd.indexOf('|');
      int secondSep = cmd.indexOf('|', firstSep + 1);

      if (firstSep != -1 && secondSep != -1) {
        currentBinId = cmd.substring(firstSep + 1, secondSep);
        currentFillLevel = cmd.substring(secondSep + 1);

        Serial.println("📥 Capture command received");
        Serial.println("🗑️ Bin: " + currentBinId);
        Serial.println("📏 Level: " + currentFillLevel);

        captureAndUpload();
      }
    }
  }
}