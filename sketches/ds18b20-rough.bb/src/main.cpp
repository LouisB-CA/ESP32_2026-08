
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define LED_A 32
#define LED_B 33
#define DELAY 150

#define ONE_WIRE_BUS 21

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int kount;

void setup() {
  Serial.begin(115200);
  pinMode(LED_A, OUTPUT);
  pinMode(LED_B, OUTPUT);
  digitalWrite(LED_A, LOW);
  digitalWrite(LED_B, LOW);

  sensors.begin();

  int deviceCount = sensors.getDeviceCount();
  Serial.print("Devices found: ");
  Serial.println(deviceCount);

  kount = 0;
}

void loop() {
    while ( kount < 20 ) {
        digitalWrite(LED_A, HIGH);
        // Serial.println("LED_A HIGH");
        delay(DELAY);
        digitalWrite(LED_A, LOW);
        // Serial.println("LED_A LOW");
        delay(DELAY);

        digitalWrite(LED_B, HIGH);
        // Serial.println("LED_B HIGH");
        delay(DELAY);
        digitalWrite(LED_B, LOW);
        // Serial.println("LED_B LOW");
        delay(DELAY);
        ++kount;
    }
    kount = 0;

    digitalWrite(LED_A, HIGH);
    digitalWrite(LED_B, HIGH);

    sensors.requestTemperatures();

    float tempC = sensors.getTempCByIndex(0);
    float tempF = sensors.getTempFByIndex(0);

    Serial.print("Raw C: ");
    Serial.println(tempC);
    delay(3*DELAY);
    Serial.print("Raw F: ");
    Serial.println(tempF);
    digitalWrite(LED_A, LOW);
    digitalWrite(LED_B, LOW);
    delay(3*DELAY);

}


