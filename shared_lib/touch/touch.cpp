#include "touch.h"
#include <Arduino.h>

// Touch-capable pin numbers are private to this module. 
// Touch pins T0/T6 give reliable readings, at least in low humidity
// tests conducted in August, 2026.  
const uint8_t TouchPadA = T6;  // GPIO14
const uint8_t TouchPadB = T0;  // GPIO4

// Number of touchRead() calls summed per measurement
// The approximate time cost will be roughly 0.5ms per touchRead() call
// Verify using micros() if the timing ever matters.
const uint8_t Samples = 16;

// Per-sample margin (below baseline) that counts as "touched"
const uint16_t PerSampleTouchMargin = 25;
const uint16_t TotalTouchMargin = Samples * PerSampleTouchMargin;

// Untouched baseline for each pad, as a SUM of Samples readings
// (not an average), measured once at startup. Baseline drifts with
// humidity and temperature, so re-measuring it at every boot is more
// robust than hardcoding one fixed threshold value.
// The static keyword at file scope tells the linker to guarantee these 
// variables and the function are private.  They cannot be seen outside this module.
static uint16_t baselineSumA;
static uint16_t baselineSumB;

// Sums several readings to smooth out sample-to-sample noise.
static uint16_t touchSampleSum(uint8_t pin) {
    uint32_t sum = 0;
    for (uint8_t i = 0; i < Samples; ++i) {
        sum += touchRead(pin);
    }
    return (uint16_t)sum;
}

void touchInit() {
    // ESP32 touch pins need no pinMode() call -- touchRead() configures
    // the pin itself. Measure baseline with the pads untouched.
    baselineSumA = touchSampleSum(TouchPadA);
    baselineSumB = touchSampleSum(TouchPadB);
}

bool touchPadATouched() {
    return touchSampleSum(TouchPadA) < (baselineSumA - TotalTouchMargin);
}

bool touchPadBTouched() {
    return touchSampleSum(TouchPadB) < (baselineSumB - TotalTouchMargin);
}

