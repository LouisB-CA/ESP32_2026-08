
# Use *pio* at the command line
## Best practice
* Make sure you have the *pio* command
```bash
ln -s ~/.platformio/penv/bin/pio ~/.local/bin/pio
```

## Using the serial monitor
* Find your board
```bash
pio device list         # expect /dev/ttyUSB0 on Fedora, Debian 13
```
* Save the serial output to a log file
```bash 
pio device monitor --port /dev/ttyUSB0 --baud 115200 | tee ~/serial_output.log
```
* Starting and stopping the PIO's built-in serial monitor
  - Use the trashcan icon to disconnect from the built-in serial monitor
  - Use the electrical power plug icon to connect to the serial monitor

## Debugging
A couple of the less obvious but very useful ones:

The upload then immediately open monitor one-liner is handy during active development — one command and you're watching output

`pio project config` is useful for debugging platformio.ini — it shows you exactly what PlatformIO has resolved, including inherited and default values you didn't explicitly set
`pio run --verbose` is the first thing to reach for when a build fails with a cryptic error

## Miscellaneous
```bash
# ── DEVICE ────────────────────────────────────────────────────────────────
pio device list                                        # show connected serial devices and ports
pio device monitor --port /dev/ttyUSB0 --baud 115200   # open serial monitor
pio device monitor --port /dev/ttyUSB0 --baud 115200 | tee ~/my_log.log  # monitor + log to file

# ── BUILD / UPLOAD ─────────────────────────────────────────────────────────
pio run                                               # build current project (must be in project dir)
pio run --target upload                               # build and upload
pio run --target upload --port /dev/ttyUSB0           # build, upload, explicit port
pio run --target clean                                # delete build artifacts
pio run --target upload --project-dir ~/project_name/sketches/clear   # upload from any directory
pio run --verbose                                     # build with full compiler output
pio run --target upload && pio device monitor --port /dev/ttyUSB0 --baud 115200  # upload then immediately open monitor

# ── PACKAGES / LIBRARIES ───────────────────────────────────────────────────
pio pkg search "DHT"                                  # search registry for a library
pio pkg install "adafruit/DHT sensor library"         # install into current project
pio pkg list                                          # list installed packages
pio pkg outdated                                      # check for updates
pio pkg update                                        # update all packages

# ── BOARDS / PLATFORMS ─────────────────────────────────────────────────────
pio boards | grep uno                                 # find board definition name
pio boards | grep esp32dev                            # find board definition name
pio pkg list                                          # show installed packages
pio pkg update                                        # update all packages

# ── PROJECT ────────────────────────────────────────────────────────────────
pio project init --board uno                          # create a new project in current dir
pio project init --board esp32dev -d ./clear          # create a new project in dir clear
pio project config                                    # dump the resolved project configuration

# ── MISC ───────────────────────────────────────────────────────────────────
pio --version                                         # show PlatformIO version
pio update                                            # update PlatformIO core itself
pio run --target upload 2>&1 | tee ~/upload.log       # capture full upload output to a log

```
