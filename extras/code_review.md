# Code Review Notes — gobi files (output/motor/analog/main + temp sketch)

These are issues found in the original files that go beyond naming/style —
things a professional review would flag. Kept here so the problems aren't
repeated in future projects, even though this project itself is stale and
won't be patched.

## Bugs / real issues

1. **Serial gets initialized twice, by two different modules.**
   `output.cpp::outputInit()` calls `Serial.begin(BAUDRATE)`. `analog.cpp::analogInit()`
   *also* calls `Serial.begin(115200)`, hardcoding the baud rate again instead
   of reusing `BAUDRATE`. Two modules think they own the serial port — exactly
   what "one owner per resource" is meant to prevent. `analogInit()` shouldn't
   touch `Serial` at all.

2. **Unbounded `sprintf` into a fixed buffer** (`output.cpp`):
   ```cpp
   char mesg[40];
   sprintf(mesg, "Initialized serial port to %ld baud.", BAUDRATE);
   ```
   The comment manually proves the buffer is big enough *for the current
   value* of `BAUDRATE` — a fragile guarantee that silently breaks if the
   value or format string ever changes. Use `snprintf(mesg, sizeof(mesg), ...)`
   so the write is bounded regardless.

3. **Headers aren't self-contained.** `motor.h` and `analog.h` use
   `uint16_t`/`int16_t` without including `<cstdint>`. They only compile
   because the `.cpp` files that use them happen to include `Arduino.h`
   first. A header should compile standalone — include what you use.

4. **No fault/error handling on either sensor path.**
   - `sensors.getTempCByIndex(0)` is used blindly; a disconnected DS18B20
     returns a sentinel value (`DEVICE_DISCONNECTED_C`, -127°C) instead of
     erroring, and nothing checks for it.
   - `HighPowerStepperDriver` exposes a status register for stall/fault
     conditions; `motor.cpp` clears status once at init and never checks it
     again during operation.

## Not wrong, but not how it'd be architected today

5. **Everything is built on blocking `delay()`.** `step()`, the LED blink
   loop, and the top-level `loop()` are all chains of `delay()`. Fine for a
   simple sketch, but the MCU can't do anything else while any delay is
   running. Once a project needs to do more than one thing concurrently
   (read a button, respond to serial, keep stepping), the standard fix is a
   non-blocking, `millis()`-based state machine instead of `delay()`.

6. **`bool dir = 0;` and direction represented as a bare `bool`.** Should be
   `bool dir = false;`. More importantly, a bare `bool` for "direction" is
   weakly typed — easy to mix up which value means which way. An
   `enum class Direction { CW, CCW };` would make misuse a compile error.

7. **`return not dir;`** — `not` is legal C++ (alternative spelling of `!`),
   but it's inconsistent with the `!`/`&&`/`||` used everywhere else in the
   codebase. Not wrong, just an unexplained style switch.
