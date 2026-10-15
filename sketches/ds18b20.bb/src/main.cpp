#include "output.h"
#include "led.h"
#include "temp.h"
#include "touch.h"
#include <Arduino.h>

// Number of alternating LED blinks per loop iteration, before each
// temperature reading.
const uint8_t BlinksPerCycle = 5;

// Delay (ms) used to space out the serial printout after a reading.
// Deliberately separate from led.cpp's blink timing -- these two
// delays happen to share a value in the original sketch, but they
// control unrelated things and shouldn't be tied together.
const uint16_t ReadoutDelayMs = 500;

void setup() {
    outputInit();  // do this first, so others can use Serial.print()
    ledInit();
    tempInit();
    touchInit();
}

void loop() {
    // check for a touch event
    while ( touchPadATouched() || touchPadBTouched() ) {
        setLED_A( touchPadATouched() );
        setLED_B( touchPadBTouched() );
    }
    setBothLeds(false);

    blinkAlternately(BlinksPerCycle);

    // Hold both LEDs on steadily while the sensor is read, as a
    // visual "busy" indicator distinct from the alternating pattern.
    setBothLeds(true);

    tempRequestReadings();

    float tempC = tempReadC();
    float tempF = tempReadF();

    Serial.print("Raw C: ");
    Serial.println(tempC);
    delay(ReadoutDelayMs);
    Serial.print("Raw F: ");
    Serial.println(tempF);

    setBothLeds(false);
    delay(ReadoutDelayMs);
}
