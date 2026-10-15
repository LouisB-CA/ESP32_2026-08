
#include <Arduino.h>

#define LED_A 32
#define LED_B 33
#define DELAY 150

void setup() {
  Serial.begin(115200);
  pinMode(LED_A, OUTPUT);
  pinMode(LED_B, OUTPUT);
  digitalWrite(LED_A, LOW);
  digitalWrite(LED_B, LOW);
}

void loop() {
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
}


