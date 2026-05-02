/**
 * camera.cpp — OV2640 Camera Implementation for AI-Thinker ESP32-CAM
 *
 * Pin mapping is specific to the AI-Thinker ESP32-CAM board.
 * The camera uses I2S parallel data bus + SCCB (I2C variant) for configuration.
 *
 * Library: esp32-camera (included in Espressif Arduino core)
 *   Install via Arduino IDE: Tools → Board Manager → esp32 by Espressif Systems
 */

#include "camera.h"
#include "config.h"

// ─── AI-Thinker ESP32-CAM Pin Definitions ─────────────────────────────────────
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1   // Not connected on AI-Thinker
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26   // SCCB Data (SDA)
#define SIOC_GPIO_NUM     27   // SCCB Clock (SCL)
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

bool camera_init() {
  camera_config_t config;

  config.ledc_channel  = LEDC_CHANNEL_0;
  config.ledc_timer    = LEDC_TIMER_0;
  config.pin_d0        = Y2_GPIO_NUM;
  config.pin_d1        = Y3_GPIO_NUM;
  config.pin_d2        = Y4_GPIO_NUM;
  config.pin_d3        = Y5_GPIO_NUM;
  config.pin_d4        = Y6_GPIO_NUM;
  config.pin_d5        = Y7_GPIO_NUM;
  config.pin_d6        = Y8_GPIO_NUM;
  config.pin_d7        = Y9_GPIO_NUM;
  config.pin_xclk      = XCLK_GPIO_NUM;
  config.pin_pclk      = PCLK_GPIO_NUM;
  config.pin_vsync     = VSYNC_GPIO_NUM;
  config.pin_href      = HREF_GPIO_NUM;
  config.pin_sscb_sda  = SIOD_GPIO_NUM;
  config.pin_sscb_scl  = SIOC_GPIO_NUM;
  config.pin_pwdn      = PWDN_GPIO_NUM;
  config.pin_reset     = RESET_GPIO_NUM;
  config.xclk_freq_hz  = 20000000;         // 20MHz XCLK
  config.pixel_format  = PIXFORMAT_JPEG;   // JPEG — smaller, faster transmission
  config.frame_size    = FRAME_SIZE;
  config.jpeg_quality  = JPEG_QUALITY;
  config.fb_count      = 1;                // 1 frame buffer (PSRAM used if available)

  // Use PSRAM if available for larger frame buffer
  if (psramFound()) {
    config.fb_location = CAMERA_FB_IN_PSRAM;
    Serial.println(F("[CAM] PSRAM found — using PSRAM for frame buffer."));
  } else {
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.frame_size  = FRAMESIZE_QVGA;   // Downsize if no PSRAM
    config.jpeg_quality = 12;
    Serial.println(F("[CAM] No PSRAM — using DRAM, downscaled to QVGA."));
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init failed: 0x%x\n", err);
    return false;
  }

  // Apply sensor settings for outdoor aerial photography
  sensor_t* s = esp_camera_sensor_get();
  s->set_brightness(s, 1);        // +1 brightness for aerial (often backlit)
  s->set_saturation(s, 0);        // neutral saturation
  s->set_contrast(s, 1);          // slight contrast boost
  s->set_whitebal(s, 1);          // auto white balance
  s->set_awb_gain(s, 1);          // AWB gain
  s->set_exposure_ctrl(s, 1);     // auto exposure
  s->set_aec2(s, 1);              // AEC DSP
  s->set_hmirror(s, 0);           // no mirror
  s->set_vflip(s, 0);             // no flip

  Serial.println(F("[CAM] OV2640 camera ready."));
  return true;
}

void camera_warmup(int frames) {
  Serial.printf("[CAM] Warm-up: discarding %d frames for exposure stabilisation...\n", frames);
  for (int i = 0; i < frames; i++) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (fb) esp_camera_fb_return(fb);
    delay(100);
  }
}

camera_fb_t* camera_capture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println(F("[CAM] Capture failed — no frame buffer."));
    return nullptr;
  }
  Serial.printf("[CAM] Captured %zu bytes (JPEG)\n", fb->len);
  return fb;
}

void camera_release_frame(camera_fb_t* fb) {
  if (fb) esp_camera_fb_return(fb);
}
