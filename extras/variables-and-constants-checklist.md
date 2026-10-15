# Variables & Constants: Quick Checklist

## Global variables & `extern`

- [ ] **Default to no globals.** Pass values in as parameters, get values
      back as return values.
- [ ] If a module needs internal state that persists between calls, make
      it a `static` variable inside that `.cpp` — not `extern`, not in
      the header. It stays invisible outside the file.
- [ ] If other files only need to *read* a module's state, expose a
      getter function instead of the variable itself (e.g.
      `sampleVoltageA()` instead of a shared `voltageA` global).
- [ ] Only use `extern` when a value truly must be shared and written
      across files (rare — `BAUDRATE` in the gobi files is the one
      example).
- [ ] If you do use `extern`: exactly **one** `.cpp` owns and defines it,
      the header just declares it, and it's easy to name the owner.
- [ ] More than a couple of `extern` globals in a project is a sign
      something should be refactored into functions instead.

## `const` vs `#define`

- [ ] **Prefer `const`.** It has a type, a scope, and shows up in the
      debugger. `#define` is just dumb text substitution with none of
      that.
- [ ] Declare `const` values at the top of the `.cpp` that uses them
      (see `DirPin`, `StepPin`, `CSPin` in `motor.cpp`) — not in the
      header, unless other files genuinely need them.
- [ ] Use `constexpr` instead of `const` when the value is known at
      compile time (array sizes, math constants) — same benefits, plus
      the compiler can optimize better.
- [ ] Reach for `#define` only for things `const` can't do: conditional
      compilation (`#ifdef DEBUG`), or platform/library macros you're
      required to use (e.g. `#define PIN_VOLTAGE_A A0` is fine because
      `A0` itself is a vendor macro).
- [ ] Never use `#define` for a value that could change type or that
      you'd want to see in a debugger — that's what `const` is for.
