#pragma once

void mqttInit(void);

bool mqttIsConnected(void);

// Reconnects to the broker if the connection has dropped. Also services
// the underlying MQTT client's internal loop -- call this regularly
// (e.g. once per main loop iteration), not just once at startup.
void mqttEnsureConnected(void);

bool mqttPublish(const char* topic, const char* payload);
