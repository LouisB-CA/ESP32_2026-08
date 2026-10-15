
# ESP32 Pin Notes (Beginner)

* Assumed board: standard **ESP32-WROOM-32 DevKit** (38-pin).
* Pin numbers are GPIO numbers, not physical pin position.
* Always check silkscreen labels on your specific board.
* Always verify your pinout diagram matches the silkscreen.

---

## Quick reference cheat sheet

- ✅ **Safe for anything:** 4, 13, 14, 16, 17, 21, 25, 26, 27, 32, 33
- ⚠️ **Reserve for SPI:** 18, 19, 23 and 22
- ⚠️ **Input-only:** 34, 35, 36, 39
- 🚫 **Avoid:** EN, 0, 1, 2, 3, 5, 12, 15
- 🚫 **Don't use at all (ESP32-WROOM-32 only):** GPIO6–11 (connected to internal flash memory)

---

## 1. Strapping pins — avoid for peripherals
| Pin | Note |
|---|---|
| GPIO0 | Must be HIGH to boot normally; LOW = flash mode |
| GPIO2 | Must be LOW or floating at boot |
| GPIO5 | Must be HIGH at boot |
| GPIO12 (MTDI) | Sets flash voltage — wrong state can brick boot |
| GPIO15 (MTDO) | Must be HIGH at boot |

**Rule:** don't wire LEDs, sensors, or buttons that pull these lines during power-up.

---

## 2. Input-only pins — avoid for outputs/LEDs/sensors needing pull-ups
- GPIO34, GPIO35, GPIO36 (VP), GPIO39 (VN)

**Rule:** fine only for simple analog/digital *inputs* only

---

## 3. Reserve for future SPI (VSPI default bus)

| Function | Pin |
|---|---|
| SCK | GPIO18 |
| MISO | GPIO19 |
| MOSI | GPIO23 |
| CS | GPI22 (also a strapping pin — see note below) |

**Rule:** reserve GPIO18/19/22/23 for future expansion if possible.

---

## 4. Best pins for a beginner project (general purpose, safe)

Good, boot-safe, output-and-input capable, internal pull-up/down available:

**GPIO4, 13, 14, 16, 17, 21, 25, 26, 27, 32, 33**

These are your "go-to" pins for LEDs, NeoPixel data, sensors, and touch.

---

