
# Design History

## Design decisions

### No wifi - no bluetooth
* The perfboard version will never be battery powered, so it does not require wifi or bluetooth.

* The perfboard version is a prototype that takes power via USB only.
<br>The perfboard will always be able to communicate via USB.

* The are neopixel signal wires within the ESP32 antenna's keep-out zone, 
so wifi/BT are unlikely to work.

