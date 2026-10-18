
# Clear the Board
***2026-10-15***<br>
A sketch to wipe the ESP32 clear of its previous programming,
<br>leaving the ESP32 outputs safe for the perfboard.

| GPIO | State | Function |
|------|-------|----------|
|  32  | High      |  DS18B20 data in/out |
|  33  | PWM      |  Yellow LED           |
|  26  | High  |  Level shifter enable |
|  27  |  Low  |  Neopixel data        |
| Others | Default  |  Not connected      |
| | | |

* The DS18B20 will remain in low power standby.
* The yellow LED can be flashed
* The level shifter is disabled.
* 


