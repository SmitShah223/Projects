/**
 * gsm_gprs.h — SIM800L GSM/GPRS Module Interface
 *
 * The SIM800L connects the aerial payload to the cellular network.
 * It operates on Quad-band (850/900/1800/1900 MHz) and supports
 * GPRS multi-slot class 12/10 for data upload.
 *
 * Key role per the project document:
 *   After image capture, the ESP32 formats the image data into an HTTP POST
 *   request and sends it to the SIM800L. The GSM module transmits this data
 *   over the GPRS connection to a designated cloud server URL.
 *
 * Wiring (ESP32-CAM → SIM800L):
 *   ESP32 GPIO 14 → SIM800L TX
 *   ESP32 GPIO 15 → SIM800L RX
 *   VCC (5V from buck converter) → SIM800L VCC
 *   GND → GND (shared)
 *
 * ⚠️  SIM800L needs 500mA–2A peak. Power from the buck converter, not ESP32 3.3V.
 */

#pragma once
#include <Arduino.h>

/**
 * Initialise the SIM800L module and verify AT communication.
 * Configures APN for GPRS data connection.
 * Returns true if module responds and network is registered.
 */
bool gsm_init();

/**
 * Establish a GPRS data connection.
 * Must be called before http_post_image().
 * Returns true on successful bearer activation.
 */
bool gsm_gprs_connect();

/** Deactivate GPRS bearer — call after data transfer to save power. */
void gsm_gprs_disconnect();

/**
 * Upload a JPEG image to the configured cloud server via HTTP POST.
 *
 * Args:
 *   data     — pointer to JPEG byte array
 *   length   — size of JPEG data in bytes
 *   filename — filename to use in the multipart form (e.g. "img_001.jpg")
 *
 * Returns true if server responded with HTTP 200.
 */
bool gsm_http_post_image(const uint8_t* data, size_t length, const char* filename);

/** Check signal strength (RSSI). Returns 0–31 (99 = unknown). */
int gsm_signal_strength();

/** Returns true if the SIM800L is registered on a network. */
bool gsm_is_registered();

/** Send a raw AT command and print the response to Serial. For debugging. */
void gsm_send_at(const char* cmd, unsigned long waitMs = 1000);
