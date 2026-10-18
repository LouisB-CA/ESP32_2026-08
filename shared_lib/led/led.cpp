
#include "led.h"
#include <Arduino.h>

// Pin number is private to this module -- nothing outside led.cpp
// needs to know which physical pin the LED is on.
const uint8_t LED = 33;

void ledInit() {
    pinMode(LED, OUTPUT);
    digitalWrite(LED, LOW);  // Initially on
}

void setLED(bool state) {
    digitalWrite(LED, state ? LOW : HIGH);
}

