#pragma once

#include <cstdint>  // uint8_t

void ledInit(void);

// Blinks LED_A and LED_B alternately, `times` times each.
void blinkAlternately(uint8_t times);

// Turns both LEDs on (true) or off (false) together.
void setBothLeds(bool state);

// Turn LEDs on (true) or off (false) separately.
void setLED_A(bool state);
void setLED_B(bool state);
