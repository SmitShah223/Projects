/**
 * rfid_handler.cpp — RC522 MFRC522 RFID Reader Implementation
 * Library: MFRC522 by miguelbalboa
 */

#include "rfid_handler.h"
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5
#define RST_PIN 0

static MFRC522 mfrc522(SS_PIN, RST_PIN);

void rfid_init() {
  SPI.begin();
  mfrc522.PCD_Init();
  mfrc522.PCD_DumpVersionToSerial();
  Serial.println(F("[RFID] MFRC522 initialised."));
}

bool rfid_cardPresent() {
  return mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial();
}

/**
 * Read the 4-byte UID and return it as a hex string (e.g. "A3B2C1D0").
 * Halts the PICC after reading so the next loop cycle is clean.
 */
String rfid_readUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  return uid;
}
