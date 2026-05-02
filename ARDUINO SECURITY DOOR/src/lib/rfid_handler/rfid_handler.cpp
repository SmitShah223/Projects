/**
 * rfid_handler.cpp — MFRC522 RFID Reader Implementation
 */

#include "rfid_handler.h"
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  10
#define RST_PIN 9

static MFRC522 mfrc522(SS_PIN, RST_PIN);

void rfid_init() {
  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println(F("[RFID] MFRC522 ready."));
}

bool rfid_cardPresent() {
  return mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial();
}

/**
 * Reads the card UID and returns it as an uppercase hex string.
 * Halts the PICC to prevent repeated reads of the same card.
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
