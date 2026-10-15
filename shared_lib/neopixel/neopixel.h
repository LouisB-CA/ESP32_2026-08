#pragma once

// =========================================================================
// neopixel.h — standalone NeoPixel (WS2812-family) driver module
// =========================================================================
//
// PURPOSE
//   Drives a single NeoPixel-compatible LED. This is a thin
//   wrapper around the FastLED library, intended as a self-contained,
//
// INDEPENDENCE
//   This module has NO knowledge of MQTT, WiFi, sensors, or any other
//   module in this project. It does not include their headers and does
//   not call their functions. Any logic that decides *what* colors to
//   show in response to external events (an MQTT message, a sensor
//   reading, etc.) belongs in the orchestrating main.cpp — never here.
//
// HOW TO USE
//   1. In setup(), call neopixelInit() once (alongside your other
//      *Init() calls like serialInit(), ledInit(), etc.).
//   2. Call neopixelSetPixel() / neopixelFill() / neopixelClear() to
//      change what's in the pixel buffer. These calls only update the
//      in-memory buffer — nothing is sent to the LEDs yet.
//   3. Call neopixelShow() to actually push the buffer to the physical
//      strip. (This two-step "set then show" pattern is standard for
//      NeoPixel-style libraries and lets you set several pixels before
//      paying the cost of a hardware update.)
//
//   Example (in main.cpp, NOT part of this module):
//       neopixelInit();
//       neopixelSetPixel(0, CRGB::Red);
//       neopixelSetPixel(1, CRGB::Orange);
//       neopixelSetPixel(2, CRGB::Green);
//       neopixelShow();
//
// COLORS
//   Colors are FastLED's CRGB type, passed directly through this
//   module's public API. FastLED predefines a large set of named
//   colors as CRGB constants, e.g.:
//       CRGB::Red, CRGB::Orange, CRGB::Yellow, CRGB::Green,
//       CRGB::Blue, CRGB::Indigo, CRGB::Violet, CRGB::White,
//       CRGB::Black (= off), and many more.
//   You can also build a color manually: CRGB(red, green, blue),
//   each channel 0-255.
//
// CONFIGURATION
//   The GPIO pin and pixel count are internal to this module (see
//   neopixel.cpp) since no other module needs to know them. To reuse
//   this module on different hardware, edit NEOPIXEL_PIN and
//   NEOPIXEL_COUNT at the top of neopixel.cpp.
//
// SCOPE / LIMITATIONS (by design, for this first version)
//   - Only ONE chain is supported (FastLED ties a chain to a pin at
//     compile time via a C++ template, so multiple independently
//     configurable chains would need separate, differently-named
//     addLeds<>() calls — out of scope for now).
//   - No getter for pixel count is provided yet. Easy to add later;
//     intentionally left out until something actually needs it.
//   - Out-of-range pixel indices passed to neopixelSetPixel() are
//     silently ignored (no crash, no error reported).
// =========================================================================

#include <FastLED.h>

// -------------------------------------------------------------------
// neopixelInit()
//   Prepares the pixel buffer and registers the chain with FastLED
//   on the configured pin. Must be called once, before any other
//   neopixel* function, typically from setup().
// -------------------------------------------------------------------
void neopixelInit();

// -------------------------------------------------------------------
// neopixelSetPixel(index, color)
//   Sets a single pixel's color in the in-memory buffer.
//     index - zero-based pixel position (0 .. count-1)
//     color - a CRGB value, e.g. CRGB::Blue or CRGB(10, 20, 30)
//   Out-of-range index values are silently ignored.
//   Does NOT update the physical LEDs — call neopixelShow() after.
// -------------------------------------------------------------------
void neopixelSetPixel(uint16_t index, CRGB color);

// -------------------------------------------------------------------
// neopixelFill(color)
//   Sets every pixel in the chain to the same color in the buffer.
//   Does NOT update the physical LEDs — call neopixelShow() after.
// -------------------------------------------------------------------
void neopixelFill(CRGB color);

// -------------------------------------------------------------------
// neopixelClear()
//   Sets every pixel to black (off) in the buffer. Equivalent to
//   neopixelFill(CRGB::Black).
//   Does NOT update the physical LEDs — call neopixelShow() after.
// -------------------------------------------------------------------
void neopixelClear();

// -------------------------------------------------------------------
// neopixelSetBrightness(brightness)
//   Sets overall brightness for the whole chain, 0 (off) - 255 (max).
//   This scales all pixel colors uniformly. Takes effect on the next
//   neopixelShow() call.
// -------------------------------------------------------------------
void neopixelSetBrightness(uint8_t brightness);

// -------------------------------------------------------------------
// neopixelShow()
//   Pushes the current buffer contents out to the physical LEDs.
//   Nothing set via neopixelSetPixel()/neopixelFill()/neopixelClear()
//   is visible on the hardware until this is called.
// -------------------------------------------------------------------
void neopixelShow();

