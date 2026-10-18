#!/usr/bin/env bash

#
# upload the 'clear' sketch to the ESP32
#
# Usage:  clear-esp32.sh [-v]
#         -v  provide verbose output (almost silent is default)
#
# N.B.    in this version, the target is not re-compiled.
#

set -euo pipefail

PROJECT_DIR="$HOME/Projects/ESP32_2026-08"

[[ "${1-}" = "-v" ]] && OPT="" || OPT="--silent"  # if argument is not -v, run almost silently

printf "Working ...\n"
if pio run --target nobuild --target upload $OPT --project-dir "$PROJECT_DIR/sketches/clear" ; then
  printf "\u2714 Success\n"
else
  printf "\u2718 Failed. Rerun with -v for verbose output.\n"
fi


