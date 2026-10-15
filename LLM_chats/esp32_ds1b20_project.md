# ESP32 Project — Chat Log (Best Practices, Refactoring, Debugging, Workflow)

A record of the conversation covering: extracting best practices from
example ("gobi") files, refactoring a monolithic sketch into modules,
a code review, header self-containment testing, an intermittent
blink-speed bug, adding touch capability, and PlatformIO workflow
questions (backups, VS Code, git vs. grep, setup procedures).

This chat was conducted with Claude Sonnet 5, over a few day period, during the second week of August, 2026.
---

## 1. Best practices document from the "gobi" example files

**Ask:** Generalize best practices for embedded C++ project structure
from 7 example files (`output.h/cpp`, `motor.h/cpp`, `analog.h/cpp`,
`main.cpp`), scoped to embedded C/C++, with a step-by-step checklist
appendix for splitting a monolithic `main.cpp` into modules.

**Result:** `embedded-cpp-best-practices.md` covering:
- One module per subsystem (`.h`/`.cpp` pair owns its pins, logic, and
  its own `xInit()`)
- Headers expose a public interface only; private helpers/constants
  stay out of the header (with a comment noting the omission was
  deliberate)
- Consistent include order in `.cpp` files: `Arduino.h` → third-party
  libs → own header
- Every module owns its own `Init()`; `main.cpp::setup()` calls them
  in explicit, commented order
- `main.cpp` stays thin — orchestration only, no hardware access or
  business logic
- Minimize and clearly document shared globals
- Comment the "why," not the "what"
- Naming conventions (`camelCase` functions, `PascalCase`/`UPPER_CASE`
  constants)
- Appendix: 10-step checklist for splitting a monolithic sketch into
  modules

---

## 2. `extern` and global variables — quick lesson

**Ask:** Explain proper use of `extern`/global variables, using the
gobi files as context, for someone more familiar with Python than C++.

**Key points:**
- In Python, modules share objects in memory automatically; in C++,
  each `.cpp` file compiles independently and knows nothing about
  other files' variables unless told via `extern`.
- Pattern: one `.cpp` **owns** the variable (defines it, gives it a
  value); the header just **declares** it as `extern` so other files
  can link to it. One owner, one `extern` declaration.
- **Use `extern`** only when a value genuinely needs to be shared and
  written across files (rare — `BAUDRATE` in `output.cpp` is the one
  example in the gobi files).
- **Don't use `extern`** for anything used inside a single module
  (pin numbers, calibration constants) — keep those local to that
  `.cpp`. Prefer passing values through function parameters/return
  values, or hiding state behind functions, over sharing raw globals.

Later folded into a separate, short checklist file,
`variables-and-constants-checklist.md`, also covering `const` vs
`#define`:
- Prefer `const` (typed, scoped, debugger-visible) over `#define`
  (blind text substitution).
- Declare `const` values at the top of the `.cpp` that uses them,
  not in the header, unless genuinely shared.
- Prefer `constexpr` for compile-time constants.
- Reserve `#define` for things `const` can't do (conditional
  compilation, vendor macros).

---

## 3. Refactoring a monolithic sketch (LED blink + DS18B20 temperature)

**Ask:** Refactor an uploaded `main.cpp` (alternating LED blink +
DS18B20 temperature read/print) per the best practices doc.

**Result:** Split into:
- `output.h/cpp` — serial init (`BAUDRATE` as the one `extern` global)
- `led.h/cpp` — owns `LedAPin`/`LedBPin` privately; exposes
  `ledInit()`, `blinkAlternate(times)`, `setBothLeds(state)`
- `temp.h/cpp` — owns the `OneWire`/`DallasTemperature` objects and
  bus pin privately; exposes `tempInit()`, `tempRequestReadings()`,
  `tempReadC()`, `tempReadF()`
- `main.cpp` — thin: calls each module's `Init()` in `setup()`
  (output first, so others can print), then orchestrates in `loop()`

Deliberate design note: the original sketch reused one delay constant
for both LED timing and post-reading serial spacing; these were split
into two independent constants (`BlinkDelayMs` in `led.cpp`,
`ReadoutDelayMs` in `main.cpp`) since they control unrelated things.

---

## 4. Code review of the original 7+1 files

**Ask:** Anything a professional would flag as genuinely wrong (not
style nitpicks) in the original files?

**Result:** `code_review.md`, covering:

**Bugs:**
1. Serial gets initialized twice — `output.cpp` and `analog.cpp` both
   call `Serial.begin()`, the second with a hardcoded baud rate.
   Violates "one owner per resource."
2. Unbounded `sprintf` into a fixed 40-byte buffer in `output.cpp` —
   safe only because the current value happens to fit; `snprintf`
   would be bounded regardless of future changes.
3. Headers (`motor.h`, `analog.h`) use `uint16_t`/`int16_t` without
   including `<cstdint>` — compiles only because whichever `.cpp`
   includes them happens to include `Arduino.h` first.
4. No fault/error checking — `getTempCByIndex()` used blindly (no
   check for the disconnected-sensor sentinel value), and the stepper
   driver's status register is never re-read after init.

**Not wrong, but not modern practice:**
5. Everything built on blocking `delay()` — fine for a simple sketch,
   but prevents doing more than one thing concurrently; the standard
   fix at scale is a `millis()`-based non-blocking state machine.
6. `bool dir = 0;` and direction represented as a bare `bool` rather
   than a typed `enum class Direction { CW, CCW };`.
7. `return not dir;` — legal C++, but an unexplained style
   inconsistency next to `!`/`&&`/`||` used elsewhere.

---

## 5. Header self-containment: "include what you use"

**Question:** How to check, using `pio run`, whether a header is
self-contained (doesn't silently rely on `Arduino.h` having been
included first by whatever `.cpp` includes it)?

**Answer:** Reorder each `.cpp`'s includes so the module's own header
comes **first**, before `Arduino.h`. If it still compiles, the header
has everything it needs on its own. This led to:
- Adding a permanent rule to the best-practices doc: a header must
  `#include` everything its own declarations need (e.g. `<cstdint>`
  for `uint8_t`/`uint16_t`), regardless of what any `.cpp` including
  it happens to pull in first — and shouldn't include something like
  `Arduino.h` unless its own declarations actually need it.
- Fixing `led.h`, which had the same missing-`<cstdint>` bug found in
  the original `motor.h`/`analog.h`.
- Recommending "own header first" as the *permanent* include order in
  every `.cpp`, so the check happens automatically on every build.

For a more rigorous, tool-based check: `pio run -t compiledb` to get
an exact `compile_commands.json`, then run that command with
`-fsyntax-only` in isolation.

---

## 6. Adding `-Wpedantic` and friends to the ESP32 cross-compiler

**Question:** How to add GCC warning flags to the Xtensa toolchain
command extracted from `compile_commands.json`?

**Answer:** Append them directly — it's a real GCC cross-build, so
standard flags apply: `-fsyntax-only -Wall -Wextra -Wpedantic`.
Expect vendor-header noise (e.g. from the ESP32 Arduino core) that
isn't your bug; filter by file path, or convert framework `-I` flags
to `-isystem` to suppress warnings from those headers specifically.
For permanent use, add `build_flags = -Wall -Wextra -Wpedantic` to
`platformio.ini` instead of doing this by hand each time.

---

## 7. The OneWire library's own `#undef` warnings

**Question:** What do these two warnings from the build log mean?
```
.pio/libdeps/esp32dev/OneWire/OneWire.cpp:599:22: warning: extra tokens at end of #undef directive
.pio/libdeps/esp32dev/OneWire/OneWire.cpp:600:20: warning: extra tokens at end of #undef directive
```

**Answer:** Harmless, and not your code — they're in the OneWire
library's own source. `#undef` only takes a macro name, but the
library's `#undef` lines have leftover macro-body text pasted after
the name (likely copy-paste residue from where `noInterrupts()`/
`interrupts()` were originally `#define`d as ESP32-specific critical-
section macros). GCC undefines the name correctly and just ignores the
extra tokens. Nothing to fix on the project side.

**Follow-up:** Could the vendored copy just be hand-edited to fix it?
Technically yes, but `.pio/libdeps/` is a PlatformIO-managed,
regeneratable directory — the edit would silently vanish on
`pio lib update`, a clean `.pio/` rebuild, or a fresh checkout on
another machine, and (per the later backup discussion) wouldn't even
survive a restic restore, since `.pio/` is excluded from backups.
Given the warning is genuinely harmless, decided not worth the
maintenance overhead of vendoring a patched copy.

---

## 8. Touch capability, and a real intermittent blink-speed bug

**Ask:** Add capacitive touch pads (two bare wires) — one lighting a
yellow LED and printing temperature, the other a red LED and printing
temperature. Also: the LED blink appeared to slow down after ~10
minutes to an hour of runtime — real, or observation error?

**Touch design:**
- New `touch.h/cpp` module; `led.h/cpp` extended with
  `setYellowLed()`/`setRedLed()` on two new pins (25, 26), since LED
  control is already that module's responsibility.
- Confirmed via search: on classic ESP32 (not S2/S3/C3), `touchRead()`
  reads **lower** on touch — opposite of the newer chip variants.
- Pin choice evolved through testing: started with `T4`/`T6`
  (GPIO13/14), then experimented with `T1`/`T5` (GPIO0/12 — both
  strapping pins) vs. `T0`/`T6` (GPIO4/14). Empirically, `T0`/`T6`
  gave a much larger, more reliable touch delta (~50–60+ vs. ~20–40),
  and as a bonus neither is a strapping pin, sidestepping the boot-mode
  risk discussion entirely.
- Threshold design evolved from a hardcoded constant → a
  self-calibrating baseline measured at `touchInit()` (since
  capacitive readings drift with humidity/temperature — a fixed
  number calibrated once goes stale) → per the user's preference, a
  **sum** of 16 raw readings (compared against a baseline sum) rather
  than an average, with the margin scaled by the sample count to
  match.
- `touchRead()` timing: ~0.5ms per call by default per Espressif's
  docs, so a 16-sample sum costs roughly 8ms per call — worth knowing
  if touch polling ever competes for time with the rest of the loop.

**Strapping pin follow-up (GPIO0 and GPIO12), verified via search:**
- **GPIO0** — genuinely determines boot vs. UART download mode, only
  sampled briefly at reset. Confirmed via `esptool`'s own docs that
  DTR/RTS from the USB-serial bridge are wired to GPIO0/EN specifically
  to enable this auto-reset-into-bootloader mechanism — which also
  explains the earlier "board slows down when the serial monitor
  disconnects" finding (see below). A bare-wire touch is capacitive,
  not a hard short to ground, so the risk is narrower than a solid
  external pull-down: it only matters if a reset happens at the exact
  instant the wire is touched.
- **GPIO12** — sets flash I/O voltage; sampled high can mismatch a
  3.3V flash chip's expectations, causing boot failures (documented,
  reproducible, including on Espressif's own forum). Has an internal
  pull-down by default, so a floating/bare wire is lower-risk than a
  hard-wired external pull-up would be. "Permanent damage" claims
  found in one source but not consistently corroborated elsewhere —
  treated as unconfirmed; failure-to-boot is the well-documented
  outcome.
- Both risks are real but bounded for a genuinely bare (not
  hard-wired) touch pad; recommended a cold-boot reliability test
  (power-cycle 15–20 times, touching the wire during some resets) as
  the empirical way to settle it for the specific hardware in use.

**Blink slowdown — resolved via the user's own experiment:**
Hypothesis (terminal scrollback choking) was ruled out by the user's
test: fresh reset → runs fast even with the monitor open, logging only
tens of bytes/min (no data volume to choke on) — but **immediately
slows down when the monitor is closed** (`Ctrl-C`'d out of
`pio device monitor`). This pointed to the auto-reset circuit: closing
the port changes the DTR/RTS lines, which are wired to `EN`/`GPIO0` on
most ESP32 dev boards specifically to enable auto-programming — and if
those lines aren't driven to a defined state after the port closes,
`EN` can end up marginal, causing intermittent partial resets that look
like a slowed blink rate from outside (repeated `setup()` re-runs)
rather than an actual clock-speed change. Proposed confirmation test:
add a single boot-time-only LED flash and see if it repeats
periodically during the "slow" phase.

---

## 9. `static` in C++: two different meanings

**Question:** Explained function-local `static` correctly (persists
between calls); asked what `static` does on module-level variables
(`baselineSumA`/`baselineSumB`) and a module-level function
(`touchSampleSum`), since those already have program-long lifetime
without it.

**Answer:** Two different jobs behind one keyword:
- Function-local `static` changes **storage duration** (lifetime).
- File-scope `static` changes **linkage** — from external (visible
  to the linker across the whole program, reachable via `extern` from
  any other file) to internal (visible only within that one `.cpp`).
  It's the mechanism-level enforcement of "this is private
  implementation detail," stronger than just leaving something out of
  the header, since it also blocks any other file from forward-
  declaring and linking to it directly.

---

## 10. A "clear" sketch for confirming fresh uploads

**Ask:** A minimal do-nothing sketch to upload before compiling/
uploading the real sketch, so a stale build vs. a fresh one is
visually distinguishable (currently the blink pattern looks identical
either way).

**Design decisions:**
- Deliberately dependency-free, single-file — no reason to be modular
  for a disposable utility, and fewer dependencies means faster
  upload cycles between real builds.
- Explicitly drives every pin the real sketches use to a known `LOW`
  state — doubles as an actual reset of leftover LED states.
- Blink pattern (slow, 1s on/off, single LED) deliberately different
  from the real app's fast alternating pair, so it's unmistakable at
  a glance.
- Suggested keeping it as its own PlatformIO project/environment
  rather than manually swapping `main.cpp` files, so running it stays
  a one-command habit.

---

## 11. Workflow discussion: directory-copying vs. git, and note-taking

**Backup exclusions:** Confirmed `.pio/` should be excluded from
restic backups, same reasoning as excluding `.venv/` — fully
regeneratable from `platformio.ini` + source, and excluding it avoids
backing up compiled objects, archived libraries, and per-board
toolchains. Restoring means running `pio run` once to regenerate,
same trade-off as `pip install -r requirements.txt`.

**Directory-copy-forward workflow (`blinky` → `blinky_dual` →
`ds18b20` → `MQTT`) vs. git:** Discussed git's tag/history model as
the standard alternative, but the user's actual retrieval need —
`find ~/Projects` + `grep` across everything ever built, months later,
across languages — is a different pattern (search-by-*what*, not
navigate-by-*when*) that directory-copying + grep serves better than
learning git archaeology would. Agreed to keep the directory-copy
approach for that reason, with two low-cost mitigations:
- When a bug is found in one copy, `grep -rn` for the same pattern
  across `~/Projects` to find and fix other copies.
- A short `NOTES.md` per sketch directory (what was added, what was
  learned, what gotcha cost time) makes `grep -rl <topic>` return
  "code + lessons," not just code.
- `git init && commit` locally, used only as a zero-learning-curve
  "undo everything" safety net before a risky edit — not as the
  retrieval/archival system.

**VS Code / split-screen gap:** Discussed `tmux`/`screen` as a
terminal-native way to get split-screen documentation-while-doing
without switching editors, but noted that live-typing polished
documentation *during* a procedure is inherently hard regardless of
tooling — the alternative already in use in this chat (narrate the
snag afterward, have it turned into a clean doc) was named as a
legitimate substitute for real-time note-taking, not just a
workaround.

---

## 12. `platformio.ini` explained, line by line

**Ask:** Explain how each line of the project's `platformio.ini` came
to be and why it's required, tied to when each capability was added.

**Result:** `platformio-ini-explained.md`, walking `blinky` →
`blinky_dual` → `ds18b20` → `MQTT`:
- `platform = espressif32` / `board = esp32dev` / `framework = arduino`
  — present from `blinky` on; explains what each selects (toolchain,
  board pin/flash/clock definition, Arduino API layer).
- `blinky_dual` — no new lines; two LEDs needed no new library.
- `ds18b20` — first `lib_deps` entries (`OneWire`,
  `DallasTemperature`); touch capability added later needed **no**
  new entry, since `touchRead()` is built into the ESP32 Arduino core.
- `MQTT` — added `PubSubClient`; **`WiFi` deliberately not listed** —
  it ships bundled with the ESP32 Arduino core, so it shows up in the
  dependency graph without needing a `lib_deps` line.
- Recommended (not yet present): `monitor_speed = 115200`, to match
  `Serial.begin(BAUDRATE)` and avoid needing `-b 115200` on every
  `pio device monitor` call.
- General lesson: an ini/config line should exist because a specific
  line of source code needs it — traceable back to a specific
  `#include`/`import`.

---

## 13. `mkdir`-to-upload procedure for the `clear` sketch (revised twice)

**First draft** assumed known values (`platform = espressif32`,
`board = esp32dev`) and used `pio project init --board esp32dev` as an
aside without justifying the board ID choice.

**Correction (user's own recalled workflow):** Should start from
device detection and permissions (`dialout` group, udev rules), then
discover the board/platform — not assume them. Also flagged that
`pio platform search` might be deprecated.

**Verified via search** against current PlatformIO docs:
- `pio platform search` is confirmed deprecated as of PlatformIO 6.0,
  replaced by `pio pkg search`.
- `pio device list` (not `pio devices`) is correct.
- `pio boards <keyword>` (e.g. `pio boards esp32`) searches across
  platforms by keyword and shows which platform each result belongs
  to — answering "which board" and "which platform" in one step,
  without needing to already know the platform name.

**Final procedure**, `setup-clear-sketch.md`:
1. **Permissions (one-time):** `pio device list` to find the port;
   `ls -l` it to find the owning group (usually `dialout` on Debian);
   `sudo usermod -a -G dialout $USER` (+ `plugdev`), log out/in; or
   install PlatformIO's udev rules file for a permanent, device-
   specific setup.
2. **Identify device/board/platform:** `pio device list` again to
   confirm the port and note the USB-bridge chip (e.g. CP2102);
   `pio boards esp32` to find the matching board ID (`esp32dev` for a
   generic/breadboard module) and its platform (`espressif32`) in one
   step; `pio platform show espressif32` to confirm `arduino` is a
   supported framework.
3. **Scaffold:** `mkdir -p clear && cd clear && pio project init --board esp32dev`
   — explained what each generated directory (`src/`, `include/`,
   `lib/`, `test/`) is for.
4. **Add `monitor_speed = 115200`** to `platformio.ini` (not set by
   `pio project init`).
5. **Write `src/main.cpp`** with the clear-sketch code from section 10
   above.
6. **Build/upload:** `pio run -t upload` (or with
   `--upload-port /dev/ttyUSB0` if auto-detection fails).
7. **Confirm:** slow single-LED blink, and/or
   `pio device monitor` printing the startup message once.
8. **Reuse from another sketch directory without recompiling:**
   `pio run -d ../clear -t upload`.

Flagged honestly at each stage that command output/behavior was
sourced from current PlatformIO documentation, not from having run it
live on this specific machine — worth checking closely against actual
output when tested.
