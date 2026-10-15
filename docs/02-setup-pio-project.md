# Setting Up and Uploading the `clear` Sketch
**Procedure for creating a new platformIO project**

* For this example, setup `sketches/clear` from scratch and get the
clear/reset sketch onto the ESP32. 

* The sample commands all run at the CLI from `ESP32_2026-08/sketches/`.

---
# 0. Powering up the board
## 0.1 Find the ESP32 on the USB bus
* What you're looking for is something like /dev/ttyUSB0 or /dev/ttyACM0.
* Expect to find not the ESP32 itself, but a UART bridge chip like
<br>the CP210x, CH340, FT232 with a specific VID:PID
* Plug the ESP32 into the USB port.  Confirm the onboard LED is on.

### Canonical method:
```bash
pio devices list | grep -B 3 -iE 'cp210|ch340|ft232'
```

Look for the entry matching your board — on most generic ESP32 dev
boards this shows up as a CP210x or CH340 USB-to-UART bridge, something
like:

```text
/dev/ttyUSB0
------------
Hardware ID: USB VID:PID=10C4:EA60
Description: CP2102 USB to UART Bridge Controller
```
### Alternative methods
* Unplug the ESP32.  Run `lsusb | sort > tmp_unplugged.txt`
* Plug the ESP32 in, Run `lsusb | sort > tmp_plugged_in.txt`
* Run `diff tmp*plug*txt` to find the device.
* Also run `sudo dmesg | grep -iE 'ttyUSB|ttyACM' | tail -1`

## 0.2 Serial port permissions (one-time, per machine)

* Before PlatformIO can talk to the board at all, the plain user must have
read/write access to its serial device. 
* On Debian, that device node is normally owned by the `dialout` group, not directly accessible to regular users.

### Find the ownership of the device
```bash
# expect this command's user:group field to show **root:dialout**
ls -l /dev/ttyUSB0   # or whatever pio device list showed
```

* If the group listed isn't one you're in, add yourself to the group
<br>and to group `plugdev`, which some tools also expect:

```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G plugdev $USER
```

* **Log out and back in** for the group change to take effect 
<br>or use `newgrp dialout` for the current shell only.

## 0.3 Install recommended udev rule
* For a more permanent, device-specific setup, PlatformIO also publishes
a udev rules file covering known board VID/PID pairs:

```bash
curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/develop/platformio/assets/system/99-platformio-udev.rules \
  | sudo tee /etc/udev/rules.d/99-platformio-udev.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

* What those udev rules actually do is they prevent Modem Manager and the mtp-probe from trying to manage or manipulate the device by setting environments variables that the Modem Manager and mtp-probe use.

* Unplug and replug the board after installing the rules file.

# 1. Confirm the device and identify the board/platform
## 1.1 Find the serial port
* Pretty much the same as above, but the exact device (/dev/tty*) may have changed.
```bash
pio devices list | grep -B 3 -iE 'cp210|ch340|ft232'
```

* Note the port (`/dev/ttyUSB0` here) — you may need it explicitly later.

* Now find the matching board definition. `pio boards` takes a search
keyword directly and shows which platform each result belongs to, so
you don't need to already know the platform name:

```bash
pio boards esp32
```

Match a row against your actual hardware — for a generic/breadboard
ESP32 module (not a name-brand dev kit like a specific Adafruit or
SparkFun board), that's normally the row with ID `esp32dev` /
"Espressif ESP32 Dev Module", 240MHz, 320KB RAM, 4MB flash. The
`Platform` column on that same row tells you the platform ID —
`espressif32` — so this one step answers both "which board" and "which
platform" together, rather than needing to discover them separately.

Confirm which frameworks that platform supports:

```bash
pio pkg show espressif32
```

Look for `arduino` in the frameworks list — that's the one this
project depends on (`Serial`, `digitalWrite()`, `pinMode()`, etc.,
rather than raw ESP-IDF calls).

*(Note: `pio platform search` also exists but is deprecated as of
PlatformIO 6.0 — the registry-wide package search is now
`pio pkg search "type:platform espressif32"`, if you ever need to
search rather than browse a known platform's boards directly.)*

# 2. Scaffold the project

```bash
# do this from the sketches directory
mkdir -p clear
pio project init --board esp32dev -d clear
```

This writes `platformio.ini` with `platform`/`board`/`framework`
filled in from the board ID you identified above, and creates the
standard layout: `src/` (your source files), `include/` (shared
headers, unused so far in this project), `lib/` (private
project-local libraries, unused — this project's libraries come from
the registry via `lib_deps` instead), and `test/` (PlatformIO's unit
test runner, unused so far).

```text
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
```

# 3. Add the one line `pio project init` doesn't set

```bash
cat >> clear/platformio.ini << 'EOF'
monitor_speed = 115200
EOF
```

Matches the sketch's `Serial.begin(115200)`, so `pio device monitor`
works without needing `-b 115200` every time. No `lib_deps` needed —
this sketch only uses `Arduino.h`, bundled with the framework.

# 4. Write `src/main.cpp`

```bash
cat > clear/src/main.cpp << 'EOF'
#include <Arduino.h>

// Pins used across this project's real sketches -- listed here so this
// clear/reset sketch can put every one of them into a known, off state,
// regardless of what the previous sketch left them doing.
const uint8_t LedAPin = 32;
const uint8_t LedBPin = 33;
const uint8_t YellowLedPin = 25;
const uint8_t RedLedPin = 26;

// Deliberately different from any blink rate the real sketches use --
// slow enough to be unmistakable at a glance as "this is the clear
// sketch," not a stale upload.
const uint16_t ClearBlinkMs = 1000;

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("CLEAR SKETCH -- board reset to blank state.");

    pinMode(LedAPin, OUTPUT);
    pinMode(LedBPin, OUTPUT);
    pinMode(YellowLedPin, OUTPUT);
    pinMode(RedLedPin, OUTPUT);

    digitalWrite(LedAPin, LOW);
    digitalWrite(LedBPin, LOW);
    digitalWrite(YellowLedPin, LOW);
    digitalWrite(RedLedPin, LOW);
}

void loop() {
    // Slow, single-LED heartbeat -- confirms this sketch is actively
    // running, not just that the board happens to be powered off.
    digitalWrite(LedAPin, HIGH);
    delay(ClearBlinkMs);
    digitalWrite(LedAPin, LOW);
    delay(ClearBlinkMs);
}
EOF
```

# 5. Build and upload

```bash
pio run -t upload -d clear
```

If PlatformIO doesn't auto-detect the port, use the one you noted in
step 1:

```bash
pio run -t upload -d clear --upload-port /dev/ttyUSB0
```

## 6. Confirm it's running

- **LED check:** `LedAPin` (GPIO32) blinks slowly — 1 second on, 1
  second off. Deliberately unlike any real sketch's cadence.
- **Serial check (optional):**
  ```bash
  pio device monitor
  ```
  Should print `CLEAR SKETCH -- board reset to blank state.` once,
  right after reset.

---

## Using it later, from another sketch directory

```bash
pio run -d ../clear -t upload
```

Uploads the already-built clear sketch without recompiling, from
wherever you're currently working.


