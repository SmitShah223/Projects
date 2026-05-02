/**
 * camera.h — ESP32-CAM OV2640 Camera Interface
 *
 * The OV2640 is the onboard 2MP camera on the AI-Thinker ESP32-CAM module.
 * It provides a 70° field of view — adequate for capturing a general area overview
 * from moderate altitude (as documented in the project results).
 *
 * The captured JPEG is stored in the ESP32's 4MB PSRAM until transmitted.
 */

#pragma once
#include <Arduino.h>
#include "esp_camera.h"

/**
 * Initialise the OV2640 camera with the AI-Thinker ESP32-CAM pin mapping.
 * Returns true on success, false on failure.
 */
bool camera_init();

/**
 * Capture a single JPEG frame and store it in PSRAM.
 * Returns a pointer to the camera frame buffer, or nullptr on failure.
 * The caller must call camera_release_frame() after use.
 */
camera_fb_t* camera_capture();

/** Release the frame buffer back to the camera driver. */
void camera_release_frame(camera_fb_t* fb);

/** Run a brief warm-up sequence (discard a few frames) to stabilise exposure. */
void camera_warmup(int frames = 3);
