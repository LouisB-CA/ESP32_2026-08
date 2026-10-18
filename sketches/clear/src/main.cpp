#include <Arduino.h>

// Pins used across this project's real sketches -- listed here so this
// clear/reset sketch can put every one of them into a known, preferred
// state, regardless of what the previous sketch left them doing.
const uint8_t LevelShifterEnable = 26;
const uint8_t LevelShifterData = 27;            // aka neopixel data pin
const uint8_t TemperatureProbeData = 32;
const uint8_t YellowLedPin = 33;

// Deliberately different from any blink rate the real sketches use --
// slow enough to be unmistakable at a glance as "this is the clear
// sketch," not a stale upload.
const uint16_t ClearBlinkMs = 500;

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("CLEAR SKETCH -- board reset to blank state.");

    pinMode(LevelShifterEnable, OUTPUT);
    pinMode(LevelShifterData, OUTPUT);
    pinMode(YellowLedPin, OUTPUT);
    pinMode(TemperatureProbeData, OUTPUT);

    digitalWrite(LevelShifterEnable, HIGH);
    digitalWrite(LevelShifterEnable, HIGH);
    digitalWrite(YellowLedPin, HIGH);
    digitalWrite(TemperatureProbeData, HIGH);
}

void loop() {
    // Slow, yellow-LED heartbeat -- confirms this sketch is actively
    // running, not just that the board happens to be powered off.
    digitalWrite(YellowLedPin, HIGH);
    delay(ClearBlinkMs);
    digitalWrite(YellowLedPin, LOW);
    delay(ClearBlinkMs);
}

