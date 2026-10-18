#include "output.h"
#include <Arduino.h>

// the following globals are declared `extern` in `output.h`
long BAUDRATE = 115200;

void outputInit() {
    Serial.begin(BAUDRATE);
    delay(500);                 // give it time to initialize
}

