#include <Arduino.h>

// Pins used across this project's real sketches -- listed here so this
// clear/reset sketch can put every one of them into a known, off state,
// regardless of what the previous sketch left them doing.
const uint8_t LedAPin = 32;
const uint8_t LedBPin = 33;
const uint8_t YellowLedPin = 25;
const uint8_t RedLedPin = 26;

// Deliberately different from any blink rate the real sketches use --
// slow enough to be unmistakable at a glance as "this is the clear
// sketch," not a stale upload.
const uint16_t ClearBlinkMs = 1000;

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("CLEAR SKETCH -- board reset to blank state.");

    pinMode(LedAPin, OUTPUT);
    pinMode(LedBPin, OUTPUT);
    pinMode(YellowLedPin, OUTPUT);
    pinMode(RedLedPin, OUTPUT);

    digitalWrite(LedAPin, LOW);
    digitalWrite(LedBPin, LOW);
    digitalWrite(YellowLedPin, LOW);
    digitalWrite(RedLedPin, LOW);
}

void loop() {
    // Slow, single-LED heartbeat -- confirms this sketch is actively
    // running, not just that the board happens to be powered off.
    digitalWrite(LedAPin, HIGH);
    delay(ClearBlinkMs);
    digitalWrite(LedAPin, LOW);
    delay(ClearBlinkMs);
}

