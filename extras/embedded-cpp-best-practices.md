# Embedded C++ Project Structure: Best Practices

## Purpose

These are the conventions we follow for structuring Arduino/embedded C++
projects. The goal is a codebase where any engineer can open a file, know
immediately what it's responsible for, and trust that it isn't hiding
surprises for other files.

This is a living document. These conventions are followed by default, but
if a real situation doesn't fit one — Appendix C's interrupt-driven case
is the current example — the right move is to add a named, explained
exception here, not to quietly deviate in code. The next engineer should
be able to tell a documented exception from an oversight.

---

## 1. One module per subsystem

Every distinct piece of hardware or functionality gets its own `.h`/`.cpp`
pair — e.g. `motor.h`/`motor.cpp`, `analog.h`/`analog.cpp`. A module owns:

- the pin assignments and constants it needs
- the low-level logic to drive that hardware
- its own initialization routine

`main.cpp` never talks to hardware directly. It only calls functions
exposed by modules.

## 1a. Goal: modules are siblings — they never call each other, never include each other's headers

A module is defined by being an isolated unit: **if two pieces of code
need to call each other, they're the same module**, not two. This is the
highest-priority goal in this document; Items 2, 3, and 6 all exist to
support it. When something needs to cross a module boundary, work through
it in this order:

1. **Default — `main.cpp` brokers it.** `main.cpp` is the only file
   allowed to know that multiple modules exist. It calls into each
   module, and when one module's output needs to reach another,
   `main.cpp` fetches it from one and passes it as a function argument
   into the other. Neither module ever names the other, and neither
   `#include`s the other's header — a module's include list is always
   just its own header, `Arduino.h`, and third-party libraries (Item 3).
2. **A getter/setter function**, if a module needs to expose state
   repeatedly or the value needs computing — still called through
   `main.cpp`, same as any other module function (Item 6, tier 2).
3. **A raw shared global, as a last resort** — a deliberate, explicit
   exception to this goal, used rarely, and only when neither of the
   above works (the canonical case is an ISR — Appendix C). When used,
   the `extern` declaration lives in whichever `.cpp` file actually
   needs it, never in a header (Item 6, tier 3).

A few things that are *not* violations of this goal:

- **Two modules independently depending on the same third-party
  library** — e.g. both `wifi.cpp` and `mqtt.cpp` including `<WiFi.h>`.
  The goal is about modules not reaching into *each other's* interfaces,
  not about sharing external libraries.
- **Init-order dependencies** (e.g. `wifiInit()` must run before any
  MQTT function is called) — these live entirely in `main.cpp::setup()`,
  with a comment explaining why, never as a call from one module into
  another (Item 4).

This is also what makes each module's `.cpp` compilable in isolation —
as its own library, with no reference to any other module (see
Appendix B for how to verify this).

## 2. Headers expose an interface, not an implementation

- Start every header with `#pragma once`.
- A header lists only the functions that other files are allowed to use.
  Everything else — pin numbers, constants, helper functions — stays
  private inside the `.cpp`.
- **A header must never declare or define a variable of any kind** — not
  a plain global, not `const`, not `extern`. Headers contain function
  declarations only, full stop. (This is about *variables*, not types: a
  header can still `#include` whatever it needs so its own function
  signatures compile — see Item 3's `CRGB` example. Using a type in a
  parameter isn't declaring a variable.)
- If a helper exists only to support another function in the same module,
  don't declare it in the header. Leave a comment showing it was
  deliberately left out, so the next person doesn't wonder if it was
  forgotten:
  ```cpp
  // Keep this one private — internal helper only
  // uint16_t readAnalogOversample(uint8_t pin);
  ```

## 3. Consistent include order in `.cpp` files — own header first

**Convention:** the module's own header comes first in its `.cpp`. After
that, `Arduino.h` and any third-party/vendor libraries (`SPI.h`,
`FastLED.h`, `WiFi.h`, etc.) follow, in whatever order is convenient —
their relative order doesn't matter functionally, since headers are
guarded (`#pragma once`) and safe to include more than once, and most
third-party libraries already pull in `Arduino.h` themselves.

Putting the module's own header first is a self-check, not a strict
compile-order requirement: it forces that header to be fully
self-sufficient. If `motor.h` secretly relies on a type or macro that
only exists because `Arduino.h` happened to be included earlier in
`motor.cpp`, the very first line of `motor.cpp` fails to compile, and
you find out immediately instead of being saved by include order.

This means a module's header must `#include` whatever it needs to make
its own declared interface compile standalone — e.g. if a function you
expose takes a `CRGB` parameter, the header includes `FastLED.h` itself
rather than assuming the includer already pulled it in. This is about
types used in function signatures, not variables — see Item 2: a header
still never declares a variable of its own.

**Never include a sibling module's header** (see Item 1a). A module
`.cpp`'s include list is always just its own header, `Arduino.h`, and
third-party libraries — never another module's `.h` file. If a module
needs a value that only a sibling can supply, that's Item 6, not an
`#include`.

**The other convention (you may see this elsewhere):** `Arduino.h` →
third-party libraries → the module's own header, last. Under that model,
headers are kept deliberately thin, and putting the module header last
guarantees any type it needs is already available from earlier includes.
Neither convention is "wrong" on its own; we use own-header-first because
the self-sufficiency check catches hidden header dependencies early.

**Checking a module compiles standalone:** since a module never
references any sibling, its `.cpp` should compile on its own with
nothing but its own header, `Arduino.h`, and whichever third-party
libraries it directly uses. See Appendix B for the exact PlatformIO
procedure to verify this.

## 4. Every module owns its own `Init()`

Each module exposes a single `xInit()` function that sets up everything it
owns (pin modes, hardware startup, default state). `main.cpp::setup()` is
just a short, ordered list of these calls:

```cpp
outputInit();   // do this first, so others can use Serial.print()
analogInit();
motorInit();
```

Order matters when one module's setup depends on another (e.g. serial must
be up before anyone prints to it) — say so in a comment at the call site,
not buried in a header.

## 5. `main.cpp` stays thin

`main.cpp` should read like a table of contents: `setup()` and `loop()`
call into modules, with little or no logic of its own. If you find
business logic, math, or hardware access creeping into `main.cpp`, it
belongs in a module instead. This is also `main.cpp`'s other job — it's
the broker described in Item 1a, so some data-fetching-and-passing
between module calls is expected here and isn't a violation of "thin."

## 6. Shared data between modules: three tiers, in order of preference

Modules are isolated (Item 1a). When two modules need to share
information, work through these in order.

**1. Function arguments through `main.cpp` (default).** `main.cpp` calls
a function on one module to get a value, then calls a function on
another module, passing that value in as an argument. Neither module
ever names the other. This is the normal case and needs nothing further
from this item.

**2. A getter (and setter, if mutable) function.** If a module needs to
expose a piece of its internal state more than once, or the value needs
computing rather than just reading, give it a small function —
`long getBaudrate();`, `void setBaudrate(long rate);` — declared in its
header like any other public function. `main.cpp` calls it and passes
the result on to whichever module needs it, exactly as in tier 1. The
value itself is never declared in a header (Item 2); only the function
is.

**3. A raw shared global — last resort, and a deliberate exception to
Item 1a.** Occasionally neither of the above works — for example, a
value that must be visible to code that can't receive arguments and
isn't called by `main.cpp` at all (interrupt service routines; see
Appendix C). When this is genuinely necessary:

- The owning module defines and initializes the variable in its own
  `.cpp`, with no `extern` keyword — this is the one and only place the
  memory is allocated:

  ```cpp
  // output.cpp — this module owns BAUDRATE
  long BAUDRATE = 115200;
  ```

- Every other file that needs to read or write it — a sibling's `.cpp`,
  or `main.cpp` — declares its own `extern` line locally, matching the
  owner's type and name exactly. This declaration goes directly in that
  `.cpp` file, **never in any header**:

  ```cpp
  // mqtt.cpp — reading a global owned by output.cpp
  extern long BAUDRATE;
  ```

  Putting the `extern` in a header instead would leak the variable to
  every file that includes that header for an unrelated reason (e.g.
  just to call the module's functions), which is exactly the kind of
  hidden cross-file surprise this document exists to prevent.

- Nothing enforces that a client's `extern` declaration matches the
  owner's real type — a mismatch compiles and links, and misbehaves at
  runtime. Keep raw shared globals rare, and prefer a getter (tier 2)
  whenever the mismatch risk isn't worth it.
- Mark clearly, at the point of definition, which module owns a global
  and who's allowed to write to it:

  ```cpp
  // output.cpp owns BAUDRATE. Read by: mqtt.cpp. Written by: output.cpp only.
  long BAUDRATE = 115200;
  ```

See Appendix C for the concrete case (ISRs) that justifies this tier.

## 7. Comment the "why," not the "what"

Code says what happens; comments should explain things that aren't
obvious from reading it — timing requirements, register/math derivations,
hardware quirks, buffer-size arithmetic. Skip comments that just restate
the line below them.

## 8. Naming conventions

- Functions: `camelCase`, verbs (`motorInit`, `setDirection`, `step`)
- Constants/pins: `PascalCase` or `UPPER_CASE`, declared `const`/`#define`
  at the top of the `.cpp` that uses them
- Keep names consistent across the module: `xInit`, `sampleX`, `setX`
- If a shared global is used (Item 6, tier 3), every `extern` declaration
  of it must match the owner's type and name exactly — nothing else
  checks this for you.

## 9. Keep files small and single-purpose

If a `.cpp` file is doing more than one job (e.g. reading sensors *and*
driving a motor), split it. A good module is easy to read top to bottom
in one sitting.

---

## Appendix A: Splitting a monolithic `main.cpp` into modules

Use this checklist when refactoring a "everything in one file" sketch:

1. **List responsibilities.** Skim the file and write down every distinct
   job it does (e.g. "reads analog voltage," "drives stepper motor,"
   "handles serial output"). Each one is a candidate module.
2. **Create a `.h`/`.cpp` pair per responsibility.** Name them after the
   subsystem, not the action (`motor.h`, not `stepping.h`).
3. **Move pin/constant definitions into the matching `.cpp`.** Nothing
   hardware-specific should remain in `main.cpp`.
4. **Move the setup code for that subsystem into an `xInit()` function**
   in the new `.cpp`. Delete it from `main.cpp::setup()` and replace it
   with a call to `xInit()`.
5. **Move the subsystem's runtime logic into functions in the new `.cpp`.**
   Give each a clear name and a minimal, purposeful set of parameters.
6. **Declare only the public functions in the header** — no variables of
   any kind (Item 2). Leave pin numbers, constants, and internal helpers
   out of it.
7. **Add `#pragma once` and the standard include order** to the new files
   (Item 3).
8. **In `main.cpp`, `#include` the new header** and replace the old
   inline code with calls to the new functions.
9. **Check init order.** If one module depends on another being ready
   (e.g. Serial before anything prints), make sure `setup()` calls them
   in the right order, with a comment explaining why.
10. **Check for sibling calls.** If the new module calls a function or
    includes a header from another module (not `Arduino.h` or a
    third-party library), that's a sign the two are really one module —
    or that the call should be replaced with the Item 1a broker pattern
    (function arguments through `main.cpp`, or a getter function, per
    Item 6).
11. **Re-read `main.cpp` alone.** It should now read like a short summary
    of the program, with no hardware details in sight. If it doesn't,
    something still needs to move into a module.

## Appendix B: Compiling a single module standalone with PlatformIO

PlatformIO's `pio ci` command builds source code without requiring a full
project — this is the standard way library authors verify a module
compiles on its own, and it's the right tool for Item 3's
standalone-compile check.

`pio ci` needs something with a `setup()`/`loop()` entry point to build
against (the Arduino framework requires one), so give the module a tiny
smoke-test sketch — this can live in an `examples/` folder alongside the
module:

```
led/
  led.h
  led.cpp
  examples/
    smoke_test/
      smoke_test.cpp
```

```cpp
// led/examples/smoke_test/smoke_test.cpp
#include "led.h"

void setup() {
  ledInit();
}

void loop() {}
```

Then, from the `led/` folder:

```bash
pio ci --lib="." --board=esp32dev examples/smoke_test/smoke_test.cpp
```

- `--lib="."` tells PlatformIO to treat the current folder (the module
  itself) as a library to build against.
- `--board=esp32dev` builds for the ESP32-WROOM target without needing a
  `platformio.ini` at all.
- The `SRC` argument (`examples/smoke_test/smoke_test.cpp`) is the entry
  point PlatformIO actually compiles and links.

If `led.cpp` or `led.h` references anything outside itself, `Arduino.h`,
and whatever third-party library it directly needs, this build fails —
which is exactly the self-sufficiency check Item 3 is for. Add
`--keep-build-dir` if you want to inspect the generated project
afterward instead of having it cleaned up automatically.

## Appendix C: Rare exception — sharing a variable with an interrupt service routine (ISR)

Interrupt service routines are the clearest justified case for Item 6's
tier 3. An ISR can't receive function arguments and isn't called by
`main.cpp`'s `setup()`/`loop()` sequence, so the usual broker pattern
doesn't apply — the ISR and the code that reads its result have to share
a variable directly.

- The variable must be `volatile`, so the compiler doesn't cache a stale
  copy in a register across the interrupt boundary.
- On ESP32 (32-bit), a single word-sized (e.g. `bool`, `uint32_t`) read
  or write is atomic, so a plain `volatile` is usually enough; a value
  that doesn't fit in one word (e.g. a 64-bit counter) needs additional
  protection — briefly disabling interrupts while reading, or a critical
  section — to avoid reading a half-updated value.

```cpp
// button.cpp — owns the ISR and the shared flag
volatile bool ButtonPressed = false;

void IRAM_ATTR buttonISR() {
  ButtonPressed = true;
}

void buttonInit() {
  pinMode(ButtonPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ButtonPin), buttonISR, FALLING);
}
```

```cpp
// main.cpp — reading a value the ISR wrote
extern volatile bool ButtonPressed;

void loop() {
  if (ButtonPressed) {
    ButtonPressed = false;
    // ...
  }
}
```

Same rule as any tier-3 global: the `extern` line lives in whichever
`.cpp` reads it, never in a header.

## Appendix D: Sharing modules across projects with a local library folder

Once a module has stabilized across a couple of projects, pull it out of
each project and keep one copy in a shared folder alongside (not inside)
your PlatformIO projects:

```
embedded/
  shared_lib/
    led/          (led.h, led.cpp)
    ds18b20/      (ds18b20.h, ds18b20.cpp)
    wifi/         (wifi.h, wifi.cpp, secrets.h)
    mqtt/         (mqtt.h, mqtt.cpp)
  blinky-project/
    platformio.ini
    src/main.cpp
  temp-mqtt-project/
    platformio.ini
    src/main.cpp
```

Each module gets its own subfolder — pointing two `lib_deps` entries at
the same folder makes them one library, not two. In each project's
`platformio.ini`:

```ini
lib_deps =
    file://../shared_lib/wifi
    file://../shared_lib/mqtt
```

(adjust the `../` depth to match how deep the project actually sits
relative to `shared_lib/`). A `file://` path is a plain local reference —
no git, no network, nothing to commit or push. Edit a module once in
`shared_lib/`, and every project referencing it picks up the change on
its next build. This fits an actively-iterating workflow well; once a
module is genuinely done, the same `lib_deps` line can later point at a
pinned git tag instead, so a project stops moving when the shared module
does — but that's a later step, not needed now.

**`secrets.h` and credentials.** `secrets.h` holds `#define WIFI_SSID ...`
/ `#define WIFI_PASSWORD ...` — macros, not variables, so it doesn't run
into Item 2's header rule — and only `wifi.cpp` includes it; nothing else
in the project sees it (Item 3). Keeping it in `shared_lib/wifi/`
alongside `wifi.cpp`, as set up here, means every project sharing this
library uses the same credentials — fine as long as that's actually true.
If a future project ever needs a different network, `secrets.h` would
need to move to be project-local instead (e.g. each project's own
`include/` folder, gitignored), with `wifi.cpp` still doing a plain
`#include "secrets.h"` that resolves to whichever project's local copy
is on that project's include path. Either way, `secrets.h` itself should
never be committed to source control — gitignore it even if you're not
using git for the shared library itself, since you may add version
control later.
