
#include <Arduino.h>

#define LED_PIN 32

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  // Serial.println("LED HIGH");
  delay(200);
  digitalWrite(LED_PIN, LOW);
  // Serial.println("LED LOW");
  delay(200);
}


