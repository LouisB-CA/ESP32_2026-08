#include "output.h"
#include "led.h"        // defines LED pin
#include "temp.h"       // defines temperature sensor pin
#include "wifi.h"
#include "mqtt.h"
#include "neopixel.h"   // defines neopixel enable and data pins
#include <Arduino.h>

// subscribers can use mosquitto_sub -h 192.168.12.12 -p 1883 -t DS18B20 -v
const char* mqtt_topic = "DS18B20";
const size_t MSG_BUFF_SIZE = 256;
char mqtt_message[MSG_BUFF_SIZE];

// Minimum loop period
const uint16_t loopDelayMs = 2500;

void setup() {
    outputInit();  // do this first, so others can use Serial.print()
    neopixelInit();
    neopixelEnable(false);
    ledInit();
    tempInit();
    wifiInit();
    delay(500);
    mqttInit();
}

void loop() {
    mqttEnsureConnected();

    setLED(true);
    tempRequestReadings();
    setLED(false);

    float tempC = tempReadC();
    float tempF = tempReadF();

    Serial.print("Raw C: ");
    Serial.println(tempC);
    snprintf(mqtt_message, MSG_BUFF_SIZE, 
        "Raw C: %8.3f, Raw F: %8.3f\0",
        tempC, tempF);
    mqttPublish(mqtt_topic, mqtt_message);
    Serial.print("Raw F: ");
    Serial.println(tempF);

    delay(loopDelayMs);
}


