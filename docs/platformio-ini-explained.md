# platformio.ini — What's In It and Why

This walks through the `platformio.ini` used across `blinky` →
`blinky_dual` → `ds18b20` → `MQTT`, explaining what each line does and
*when/why* it got added, so future-you (or a future project) doesn't
have to reverse-engineer it from scratch.

Reconstructed from the build log and project history — check against
your actual file for anything that doesn't match.

---

## The lines that were there from `blinky` on

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
```

- **`[env:esp32dev]`** — Names this build configuration. PlatformIO
  supports multiple named environments in one file (e.g. `env:esp32dev`
  and `env:clear`, as discussed for the clear-sketch idea); `esp32dev`
  here is just a label, not a magic keyword — it happens to match the
  board name because that's a natural name to pick, not because it has
  to.
- **`platform = espressif32`** — Tells PlatformIO which chip family's
  toolchain, SDK, and build tools to install and use (the Xtensa
  compiler, esptool, the ESP-IDF-based build system underneath Arduino).
  This is the "what kind of chip" line.
- **`board = esp32dev`** — Selects the specific board definition:
  pin mappings, flash size, default clock speed, upload/monitor
  defaults. Changing boards (e.g. to an ESP32-S3 dev board) means
  changing this line, and potentially your pin numbers too, since
  strapping pins and touch-capable GPIOs differ by chip variant (as we
  ran into with the touch pad choice).
- **`framework = arduino`** — Says you want the Arduino API/core layered
  on top of ESP-IDF, rather than writing directly against ESP-IDF. This
  is why `Arduino.h`, `Serial`, `digitalWrite()`, etc. are available at
  all.

At this stage there's no `lib_deps` — `blinky` only uses `Arduino.h`
itself, which comes bundled with the framework, so nothing extra needs
to be fetched.

## `blinky_dual`

No new `platformio.ini` lines. Two LEDs instead of one is still just
`digitalWrite()`/`pinMode()` — no new library, so nothing to declare.
Worth noting explicitly: **not every capability change requires an ini
change** — only ones that pull in code PlatformIO doesn't already have.

## `ds18b20` — first `lib_deps` entries

```ini
lib_deps =
    OneWire
    DallasTemperature
```

- **`lib_deps`** — Tells PlatformIO's Library Dependency Finder which
  external libraries to fetch (from the PlatformIO/Arduino library
  registry) and link into the build. Without this, `#include
  <OneWire.h>` and `#include <DallasTemperature.h>` in `temp.cpp` would
  fail — those aren't part of the Arduino core, they're third-party
  libraries the DS18B20 sensor needs.
- **Why both, when only `DallasTemperature` is used directly?**
  `DallasTemperature` is itself built on top of `OneWire` (the DS18B20
  talks over a 1-Wire bus) — it's a dependency of a dependency. PlatformIO
  can often resolve transitive dependencies automatically, but declaring
  both explicitly here means the exact library set is documented in the
  file itself rather than left to auto-resolution.

The touch capability added later (`touchRead()`) needed **no** new
`lib_deps` line — touch support is built into the ESP32 Arduino core
itself, not a separate library. Same category as `blinky_dual`: new
capability, no new dependency.

## `MQTT` — the WiFi/MQTT entries

```ini
lib_deps =
    OneWire
    DallasTemperature
    PubSubClient
```

- **`PubSubClient`** — Added because `mqtt.cpp` includes
  `<PubSubClient.h>`, and MQTT isn't part of the Arduino core; this is
  the library doing the actual MQTT protocol work.
- **Notice `WiFi` is *not* listed here, on purpose.** `<WiFi.h>` in
  `wifi.cpp` doesn't need a `lib_deps` entry because, unlike
  `PubSubClient`, WiFi support ships bundled with
  `framework-arduinoespressif32` itself — it's part of the ESP32 Arduino
  core, not a registry library. The build log's dependency graph still
  lists it (`WiFi @ 2.0.0`) because PlatformIO reports every library it
  resolves, framework-bundled or not — but you don't *declare* the
  bundled ones. Worth remembering for next time: if `#include <X.h>`
  works with zero `lib_deps` entry and the build still finds it, that's
  usually a sign X ships with the framework rather than being a project
  dependency of yours.

## Worth adding, not yet present (optional but recommended)

```ini
monitor_speed = 115200
```

Without this, `pio device monitor` defaults to a different baud rate
than your sketch's `Serial.begin(BAUDRATE)`, so you'd need `-b 115200`
on the command line every time (as you've been doing). Setting it once
here means plain `pio device monitor` just works, matching whatever
`BAUDRATE` your `output.cpp` module uses.

---

## The general lesson, for the next language/board

The pattern that generalizes past this ESP32 project: **an ini/config
file line should exist because something in the source code needs it
to exist.** Every entry here traces back to a specific `#include` in a
specific `.cpp` file. When you're staring at an unfamiliar `.ini`,
`Cargo.toml`, or `requirements.txt` months from now, the fastest way
back in isn't memorizing syntax — it's asking "which file needs this,
and why" and grepping your own source for the matching include/import.
