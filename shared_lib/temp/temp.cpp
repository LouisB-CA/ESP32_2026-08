#include "temp.h"
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Bus pin and sensor objects are private to this module -- other
// files only ever talk to the sensor through the functions below.
const uint8_t OneWireBusPin = 21;

OneWire oneWire(OneWireBusPin);
DallasTemperature sensors(&oneWire);

void tempInit() {
    sensors.begin();

    int deviceCount = sensors.getDeviceCount();
    Serial.print("Devices found: ");
    Serial.println(deviceCount);
}

void tempRequestReadings() {
    // Starts a conversion on all sensors on the bus. For 12-bit
    // resolution (the DS18B20 default) this can take up to ~750ms,
    // so callers should expect this to block briefly.
    sensors.requestTemperatures();
}

float tempReadC() {
    return sensors.getTempCByIndex(0);
}

float tempReadF() {
    return sensors.getTempFByIndex(0);
}
