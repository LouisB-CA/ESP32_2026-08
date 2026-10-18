// =========================================================================
// neopixel.cpp — implementation for neopixel.h
//
// See neopixel.h for the public API, usage pattern, and design notes.
// =========================================================================

// FASTLED_ESP32_RMT must be defined BEFORE FastLED.h is included.
// It tells FastLED to use the ESP32's RMT peripheral to generate the
// NeoPixel timing signal instead of FastLED's default bit-banged
// approach. This matters because this project also runs WiFi (see
// wifiInit()/mqttInit() elsewhere) — WiFi's interrupts can corrupt
// bit-banged NeoPixel timing and cause flickering or glitched colors.
// RMT is hardware-timed and immune to that.
#define FASTLED_ESP32_RMT

#include "neopixel.h"
#include <Arduino.h>    // declares digitalWrite, LOW, HIGH

// -------------------------------------------------------------------
// Module configuration — internal to this module only.
// No other module needs to know the pin or pixel count, so these
// are not exposed in neopixel.h. Edit these two lines to reuse this
// module with different hardware.
// -------------------------------------------------------------------

static const uint8_t  NEOPIXEL_ENABLE = 26;  // set low to enable
static const uint8_t  NEOPIXEL_DATA   = 27;  // ESP32 GPIO driving the chain
static const uint16_t NEOPIXEL_COUNT  =  3;  // pixel chain buffer size in pixels

// LED chipset assumption: WS2812 (the common NeoPixel part). FastLED's
// default color order for WS2812 is GRB, which matches how these strips
// are wired in practice — no color-order correction needed here.

// Pixel buffer — one CRGB entry per pixel. This is the in-memory
// "canvas" that neopixelSetPixel()/neopixelFill()/neopixelClear()
// write into, and that neopixelShow() sends to the hardware.
static CRGB leds[NEOPIXEL_COUNT];

// -------------------------------------------------------------------
// neopixelInit()
//   Registers the pixel buffer with FastLED on GPIO pin NEOPIXEL_DATA.
//   FastLED's addLeds<>() call requires the chipset and pin as
//   template parameters — they must be known at compile time. This
//   is why NEOPIXEL_DATA is a fixed constant above rather than a
//   runtime argument to this function (see the design discussion in
//   neopixel.h for background).
// -------------------------------------------------------------------
void neopixelInit() {
    pinMode(NEOPIXEL_ENABLE, OUTPUT);
    neopixelEnable(true);
    FastLED.addLeds<WS2812, NEOPIXEL_DATA, RGB>(leds, NEOPIXEL_COUNT);
    neopixelClear();
    neopixelSetBrightness(128);
    neopixelShow();
}

// -------------------------------------------------------------------
// neopixelSetPixel(index, color)
//   Writes one entry in the pixel buffer. Bounds-checked: an index
//   at or beyond NEOPIXEL_COUNT is silently ignored, by design (see
//   neopixel.h) rather than crashing or logging an error.
// -------------------------------------------------------------------
void neopixelSetPixel(uint16_t index, CRGB color) {
    if (index >= NEOPIXEL_COUNT) {
        return;  // silent no-op on out-of-range index
    }
    leds[index] = color;
}

// -------------------------------------------------------------------
// neopixelFill(color)
//   Writes the same color into every entry of the pixel buffer.
// -------------------------------------------------------------------
void neopixelFill(CRGB color) {
    fill_solid(leds, NEOPIXEL_COUNT, color);
}

// -------------------------------------------------------------------
// neopixelClear()
//   Writes black (off) into every entry of the pixel buffer.
// -------------------------------------------------------------------
void neopixelClear() {
    neopixelFill(CRGB::Black);
}

// -------------------------------------------------------------------
// neopixelSetBrightness(brightness)
//   Delegates to FastLED's global brightness scaling, which applies
//   to this chain when neopixelShow() is next called.
// -------------------------------------------------------------------
void neopixelSetBrightness(uint8_t brightness) {
    FastLED.setBrightness(brightness);
}

// -------------------------------------------------------------------
// neopixelShow()
//   Sends the current pixel buffer to the physical LEDs.
// -------------------------------------------------------------------
void neopixelShow() {
    FastLED.show();
}

// -------------------------------------------------------------------
// neopixelEnable(boolean)
//   Enable the levelshifter.
// -------------------------------------------------------------------
void neopixelEnable(bool flag) {
    if (flag) {
        digitalWrite(NEOPIXEL_ENABLE, LOW);
    } else {
        digitalWrite(NEOPIXEL_ENABLE, HIGH);
        digitalWrite(NEOPIXEL_DATA,   HIGH);
    }
}

