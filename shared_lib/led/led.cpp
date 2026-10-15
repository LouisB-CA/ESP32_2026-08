
#include "led.h"
#include <Arduino.h>

// Pin numbers are private to this module -- nothing outside led.cpp
// needs to know which physical pins the LEDs are on.
const uint8_t LED_A = 32;
const uint8_t LED_B = 33;

// On/off duration (ms) for each half-step of the alternating blink.
const uint16_t BlinkDelayMs = 150;

void ledInit() {
    pinMode(LED_A, OUTPUT);
    pinMode(LED_B, OUTPUT);
    digitalWrite(LED_A, LOW);
    digitalWrite(LED_B, LOW);
}

void blinkAlternately(uint8_t times) {
    for (uint8_t i = 0; i < times; ++i) {
        digitalWrite(LED_A, HIGH);
        delay(BlinkDelayMs);
        digitalWrite(LED_A, LOW);
        delay(BlinkDelayMs);

        digitalWrite(LED_B, HIGH);
        delay(BlinkDelayMs);
        digitalWrite(LED_B, LOW);
        delay(BlinkDelayMs);
    }
}

void setBothLeds(bool state) {
    digitalWrite(LED_A, state ? HIGH : LOW);
    digitalWrite(LED_B, state ? HIGH : LOW);
}

void setLED_A(bool state) {
    digitalWrite(LED_A, state ? HIGH : LOW);
}

void setLED_B(bool state) {
    digitalWrite(LED_B, state ? HIGH : LOW);
}

