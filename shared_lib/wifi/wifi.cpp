#include "wifi.h"
#include "secrets.h"
#include <Arduino.h>
#include <WiFi.h>

// How long to wait for an initial connection before giving up, in ms.
const uint32_t WifiConnectTimeoutMs = 15000;

void wifiInit() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFISSID, WIFIPASSWORD);

    Serial.print("Connecting to WiFi");
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED &&
           (millis() - start) < WifiConnectTimeoutMs) {
        delay(250);
        Serial.print(".");
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("WiFi connected, IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("WiFi connection failed (timed out).");
    }
}

bool wifiIsConnected() {
    return WiFi.status() == WL_CONNECTED;
}
