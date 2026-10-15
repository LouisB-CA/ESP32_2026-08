#include "mqtt.h"
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Broker settings are private to this module -- fill these in for your
// setup. Nothing outside mqtt.cpp needs to know them.
const char* MqttBrokerHost = "192.168.12.12";
const uint16_t MqttBrokerPort = 1883;
const char* MqttClientId = "esp32-temp-sensor";

// PubSubClient needs an underlying network client; WiFiClient is the
// plain (non-TLS) one that matches wifi.cpp's WiFi.h connection.
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void mqttInit() {
    mqttClient.setServer(MqttBrokerHost, MqttBrokerPort);
}

bool mqttIsConnected() {
    return mqttClient.connected();
}

void mqttEnsureConnected() {
    // PubSubClient can silently drop the connection on a network hiccup;
    // this reconnects if needed. Safe to call on every loop iteration.
    if (!mqttClient.connected()) {
        Serial.print("Connecting to MQTT broker...");
        if (mqttClient.connect(MqttClientId)) {
            Serial.println("connected.");
        } else {
            Serial.print("failed, rc=");
            Serial.println(mqttClient.state());
        }
    }

    // Must be called regularly regardless of connection state -- this is
    // what actually keeps the connection alive and processes traffic.
    mqttClient.loop();
}

bool mqttPublish(const char* topic, const char* payload) {
    if (!mqttClient.connected()) {
        return false;
    }
    return mqttClient.publish(topic, payload);
}
