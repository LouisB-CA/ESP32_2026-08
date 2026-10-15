# Working with `shared_lib` in PlatformIO Projects

## Background: why this matters

`platformio.ini` pulls the shared library in via:

```
lib_deps =
    file://../../shared_lib/
```

PlatformIO does **not** compile directly from `../../shared_lib/` on every
build. The first time a project resolves that dependency, it **copies**
the library's files into:

```
<project>/.pio/libdeps/esp32dev/shared_lib/
```

That copy — not the original in `../shared_lib/` — is what actually gets
compiled from then on. `pio run -t clean` only removes build artifacts
(`.pio/build/`); it does **not** refresh or remove the `libdeps` copy.
So editing `../shared_lib/neopixel.cpp` and re-running `clean` + `upload`
can silently build against a stale copy that no longer matches your edits.

This is exactly what happened when a color-order fix in `shared_lib/`
didn't change the LED's behavior — the build was still using an old
cached copy in `.pio/libdeps/`.

**The reliable fix, confirmed working:**

```
rm -rf ./neopixel/.pio
```

(Deleting the whole `.pio` directory, not just the `libdeps/shared_lib`
subfolder — the build artifacts and the libdeps copy both need to go, or
the two can get out of sync with each other too.)

`pio run -t clean` is not a substitute for this — it doesn't touch
`libdeps/` at all. Note also that `pio run -t clean` has been observed
to segfault in this environment on at least one occasion (unrelated to
this workflow) — if it does, that's a separate issue to investigate
later, not something to depend on for a correct rebuild in the meantime.

## Recommended workflow: develop locally, promote when stable

Given the caching behavior above, don't develop directly against
`shared_lib/` — every edit-test cycle would need a full `.pio` wipe,
which is slow and easy to forget. Instead:

### 1. Develop the module inside the sketch project itself

Keep `neopixel.h` / `neopixel.cpp` in `./neopixel/src/` (alongside
`main.cpp`) while actively iterating. Local `src/` files are picked up
directly by PlatformIO on every build — no copy step, no caching layer,
no stale-file risk. Edit, build, upload, repeat, normally.

### 2. Finalize the module

Once the module is complete and tested — matches the header/cpp split,
naming conventions, and independence rules already established for this
project's modules — treat it as done.

### 3. Promote it to `shared_lib/`

Move (not copy-and-leave-both) the finished `.h`/`.cpp` pair from
`./neopixel/src/` into `../shared_lib/`:

```
mv ./neopixel/src/neopixel.h ./neopixel/src/neopixel.cpp ../shared_lib/
```

Then remove the `#include` reference from being satisfied locally — since
the files are gone from `src/`, `lib_deps`'s `file://../../shared_lib/`
entry now supplies them instead.

### 4. Force a clean pull of the newly promoted files

Because this is the *first* time this project resolves this exact
version of the file from `shared_lib/`, do the full wipe once to be
safe:

```
rm -rf ./neopixel/.pio
pio run -d neopixel -t upload
```

### 5. Verify

Confirm the sketch builds and behaves correctly using the version now
living in `shared_lib/`, not the local copy (which no longer exists).

## Updating an already-promoted module later

If a bug or improvement is needed in a module that's already live in
`shared_lib/` (used by this project and possibly others):

1. Edit the file directly in `../shared_lib/`.
2. For **every** project that depends on it, before your next test:
   ```
   rm -rf ./<project>/.pio
   ```
3. Rebuild/upload as normal.

This is more disruptive than local `src/` development (full rebuild of
everything, every project, every edit), which is the main reason to
prefer developing new/changed modules locally first and only touching
`shared_lib/` once a module is stable.

## Quick reference

| Situation                                      | Command                                  |
|-------------------------------------------------|-------------------------------------------|
| Iterating on a new module                       | Keep it in `./<project>/src/`, build normally |
| Promoting a finished module to `shared_lib/`    | `mv` files, then `rm -rf ./<project>/.pio`, then rebuild |
| Fixing a bug in an already-shared module        | Edit in `../shared_lib/`, then `rm -rf ./<project>/.pio` for **each** dependent project |
| "It's not picking up my shared_lib edit"        | `rm -rf ./<project>/.pio` (not `pio run -t clean`) |
