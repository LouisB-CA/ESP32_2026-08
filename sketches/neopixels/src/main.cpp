#include "output.h"
#include "led.h"        // defines LED pin
#include "neopixel.h"   // defines neopixel enable and data pins
#include <Arduino.h>

// Minimum loop period
const uint16_t loopDelayMs = 500;

void setup() {
    outputInit();  // do this first, so others can use Serial.print()
    ledInit();
    neopixelInit();
    delay(500);
    neopixelEnable(true);
    neopixelClear();
    setLED(false);
}

void loop() {
    // neopixelSetPixel(2, CRGB::Red);
    // neopixelSetPixel(1, CRGB::Green);
    neopixelSetPixel(0, CRGB::Green);
    neopixelSetBrightness(96);
    neopixelShow();
    delay(loopDelayMs);
}



