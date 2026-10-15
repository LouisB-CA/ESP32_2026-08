#!/usr/bin/env bash
#
# try_color_orders.sh
#
# Run this from the directory that CONTAINS the "neopixel" project dir,
# i.e. the same place you've been running `vi ../shared_lib/neopixel*`
# from (so shared_lib/ and neopixel/ are siblings from here).
#
# What it does, for each candidate FastLED color order:
#   1. Edits the addLeds<> color-order token in shared_lib/neopixel.cpp
#   2. Wipes every layer of cache that could serve a stale copy:
#        - pio pkg clean       (PlatformIO's own package/dep cache)
#        - rm -rf .pio         (build artifacts AND the libdeps copy
#                                that caused last time's stale build)
#        - pio run -t clean    (belt and suspenders)
#   3. Uploads fresh
#   4. Pauses and asks you what color you actually saw
#
# main.cpp is left untouched, per your instruction — it already sets
# CRGB::Red (steady) and CRGB::Black (off) in its loop, which is enough
# to visually check each variation.
#
# Exits immediately on any command failure (set -e) so a build/upload
# error doesn't silently get skipped as if it were a color result.

set -e

SHARED_LIB_CPP="../shared_lib/neopixel.cpp"
PROJECT_DIR="neopixel"

# All 6 permutations of R, G, B — in case the "obvious" two (RGB, GRB)
# aren't actually the right one for this specific part.
ORDERS=(RGB GRB RBG BRG GBR BGR)

if [ ! -f "$SHARED_LIB_CPP" ]; then
    echo "ERROR: $SHARED_LIB_CPP not found relative to $(pwd)."
    echo "Run this script from the directory containing '$PROJECT_DIR/'."
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: project dir '$PROJECT_DIR' not found relative to $(pwd)."
    exit 1
fi

echo "Testing FastLED color orders: ${ORDERS[*]}"
echo "Editing: $SHARED_LIB_CPP"
echo "Project: $PROJECT_DIR"
echo

for ORDER in "${ORDERS[@]}"; do
    echo "============================================================"
    echo "Setting color order to: $ORDER"
    echo "============================================================"

    # Replace the color-order token (3rd template arg) in the
    # FastLED.addLeds<WS2812, NEOPIXEL_PIN, XXX> line. Only touches
    # that one token; leaves pin/count/everything else alone.
    sed -i -E \
        "s/(FastLED\.addLeds<WS2812, *NEOPIXEL_PIN, *)[A-Z]+(>)/\1${ORDER}\2/" \
        "$SHARED_LIB_CPP"

    # Show the resulting line so you can visually confirm the edit
    # landed correctly, not just trust the sed exit code.
    echo "Resulting addLeds line:"
    grep "FastLED.addLeds" "$SHARED_LIB_CPP"
    echo

    # Clear every cache layer that could serve a stale copy of
    # neopixel.cpp instead of the one we just edited.
    pio pkg update -d "$PROJECT_DIR"
    rm -rf "./${PROJECT_DIR}/.pio"
    pio run -t clean -d "$PROJECT_DIR"

    echo "Uploading with color order = $ORDER ..."
    pio run -t upload -d "$PROJECT_DIR"

    echo
    echo "Look at the LED now. main.cpp cycles it Red / Black."
    read -r -p "What color did you actually see for ORDER=$ORDER? (type it, or press Enter to skip) " OBSERVED
    echo "Logged: ORDER=$ORDER -> observed='$OBSERVED'" >> color_order_results.txt
    echo
done

echo "============================================================"
echo "Done. Results saved to color_order_results.txt:"
echo "============================================================"
cat color_order_results.txt
