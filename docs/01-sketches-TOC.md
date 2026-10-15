

# Table of Contents for Sketches

### 1. blinky
* Obsolete.  Used to blink one LED while trying to figure out the pinout diagram.
* Turns out, had the pinout diagram was not for the Expressif ESP32-WROOM Dev Kit C.
* This version used a LED+resistor dangling from the dev board.

### 2. blinky_dual
* Obsolete.  Blinks two LEDs, both dangling from dev board.

### 3. ds18b20-rough
* Move the dual blinky hardware to a breadboard.
* Add the DS18B20 digital temperature sensor to the dual blinky sketch.
* Provide temperature readings to the serial monitor.
* Deprecated.  This sketch has everything in one main.cpp.
* TODO: separate the different program modules by function.

### 4. ds18b20
* Separate the previous rough version into code modules according to each hardware domain.
* Add module for using capacitative touch pins
* Retain serial output

### 5. MQTT
* Remove capacitative touch features
* Add MQTT capabilites









