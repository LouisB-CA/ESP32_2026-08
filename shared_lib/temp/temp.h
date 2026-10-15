#pragma once

void tempInit(void);

// Triggers a temperature conversion on all sensors on the bus.
// Must be called once before tempReadC() / tempReadF().
void tempRequestReadings(void);

float tempReadC(void);
float tempReadF(void);
