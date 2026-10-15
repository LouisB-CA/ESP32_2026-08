# shared_lib

Code in this directory is shared across all the sketches in `sketches/`. 
This code is not a normal PlatformIO project on its own — it is a set of 
small "modules" that PlatformIO's Library Dependency Finder (LDF) picks up 
and compiles directly into whichever sketch uses them.

## How it works

Each subdirectory here (`neopixel/`, `temp/`, `mqtt/`, `wifi/`, `led/`, `output/`,
`touch/`) is treated by PlatformIO as its own private library. The folder name
*is* the library name — there's no manifest file required to make that happen.

A sketch pulls in a module the normal way: by `#include`-ing its header
(e.g. `#include "neopixel.h"`) from `src/main.cpp`. From there, LDF follows the
chain: it looks at what that module's own source files `#include`, resolves
those too, and keeps going until everything needed is found. This is why the
build log shows a "Dependency Graph" listing exactly which modules got pulled in.

There is no separate compile or install step for this code. Every time you build
a sketch, PlatformIO recompiles whatever modules that sketch uses, straight from
the source files in this directory. There's no cached "library build" to go stale
— if you edit a `.cpp` here, the next `pio run` in any sketch that uses it will
pick up the change.

## What gets included in a build — and what doesn't

**Included:** only the modules a sketch actually references, directly or
transitively. If `src/main.cpp` includes `neopixel.h`, the `neopixel/` module
is compiled. If `neopixel.cpp` in turn includes something from `output/`, that
gets pulled in too, automatically.

**Excluded:** every module *not* reachable from the sketch's `#include` chain.
There's no exclude list to maintain — a sketch that never includes `mqtt.h`
will never compile `mqtt.cpp`, and will never need MQTT's dependencies
installed. This is the whole reason the code was split into per-module
subdirectories instead of one big `shared_lib` blob: each sketch only pays for
what it uses.

## Editing existing code

- **Adding new functions is safe.** Nothing else in `shared_lib` or any sketch
  references code that doesn't exist yet, so new additions can't break another
  project.
- **Changing an existing function's signature, return type, or behavior is
  risky.** Because this code is shared, a change made while working on one
  sketch can silently break a *different* sketch that also uses this module,
  and you won't necessarily see that until you build (or run) the other
  project. If you need to change how something behaves, it's worth checking
  which sketches use that module first, and considering whether to add a new
  function instead of changing an existing one.

## What your sketch's `platformio.ini` needs

Every sketch that uses `shared_lib` needs one line telling PlatformIO where to
look for these private libraries:

```ini
lib_extra_dirs = $PROJECT_DIR/../../shared_lib
```

That's it for the modules themselves — no per-module registration is needed
beyond this single line. What you *also* need is any third-party library that
your included modules depend on (see below).

## Third-party dependencies: do you need one, and which?

Some modules wrap a third-party library — `neopixel` needs FastLED, `temp`
needs OneWire and DallasTemperature, `mqtt` needs PubSubClient. PlatformIO does
**not** figure this out for you automatically for locally-written modules like
these, so you have to declare them yourself in the sketch's `lib_deps`.

To find out what a given module needs:

1. Check that module's own `README.md` (each one lists its dependencies).
2. Or look for `#include <...>` lines at the top of its `.cpp`/`.h` files that
   *aren't* another `shared_lib` module and aren't part of the Arduino/ESP32
   framework.
3. Or just try building — a missing dependency shows up as a `fatal error: ...
   No such file or directory` naming the exact header PlatformIO couldn't find.

Only list the dependencies for modules your sketch actually uses. For example,
a sketch that only uses `mqtt` and `wifi` needs:

```ini
lib_deps =
    knolleary/PubSubClient
```

A sketch that uses `neopixel`, `temp`, `mqtt`, and `wifi` together needs:

```ini
lib_deps =
    paulstoffregen/OneWire @ ^2.3.7
    milesburton/DallasTemperature @ ^3.11.0
    knolleary/PubSubClient
    fastled/FastLED @ ^3.9.2
```

**Exception — framework-bundled libraries:** `WiFi` (and other libraries that
ship with `framework-arduinoespressif32`, like `Preferences` or `FS`) don't
need a `lib_deps` entry at all. PlatformIO finds these automatically the same
way it finds them for your sketch's own `main.cpp`.

## Adding a new module

Create a new subdirectory here with your `.cpp`/`.h` files directly inside it
(no nested `src/` folder needed) and, if it wraps a third-party library, a
short `README.md` stating what to add to `lib_deps`. No other registration is
required — the first sketch that `#include`s its header will pull it into the
build.

## Lessons learned / things that don't work

A couple of approaches were tried and abandoned before landing on the setup
above — worth knowing in case you're tempted to reach for them again:

- **A build script calling `env.BuildSources()`** (via `extra_scripts`) was
  used originally to compile all of `shared_lib` into every sketch. It ran
  into a real conflict: `BuildSources()` only works from a `pre:` script, but
  a `pre:` script runs *before* PlatformIO has resolved `lib_deps`, so
  third-party headers weren't found yet. Running it as `post:` fixed that but
  then failed differently, since by `post:` time the sketch's build target is
  already finalized and no more sources can be injected into it. `lib_extra_dirs`
  sidesteps this entirely by letting LDF do the discovery natively, with
  correct timing, and without a custom script.
- **A `library.json` manifest per module**, with third-party libraries listed
  under `"dependencies"`, was tried as a way to avoid repeating `lib_deps` in
  every sketch. It parses fine but does nothing: PlatformIO's LDF does not
  auto-install dependencies listed in a *private* library's manifest (this is
  a known PlatformIO limitation, not a config mistake). The third-party
  library still has to be listed in the sketch's own `lib_deps`. The
  per-module `README.md` files replace those manifests — same information,
  but honest about the fact that it's documentation, not automation.
