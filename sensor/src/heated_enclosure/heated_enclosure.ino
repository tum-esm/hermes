// pass variables from outside
#include "config.h"

// https://github.com/PaulStoffregen/OneWire
#include <OneWire.h>

// https://github.com/milesburton/Arduino-Temperature-Control-Library
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2  // sensor DS18B20 on digital pin 2
#define HEATER 4 // control of heater relais
#define FAN 3 // control of fan relais

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
float measured_temperature;

void setup(void) { 
  Serial.begin(9600);
  sensors.begin();
  pinMode(HEATER,OUTPUT);
  pinMode(FAN,OUTPUT);
  digitalWrite(HEATER,LOW);
  digitalWrite(FAN,LOW);
} 

void loop(void){ 
  if(sensors.getDS18Count() == 0){
    Serial.println("no temperature sensor");
    digitalWrite(HEATER,LOW);
    digitalWrite(FAN,LOW);
  }

  // there can be more than one temperature sensor on the databus
  sensors.requestTemperatures(); 
  measured_temperature = sensors.getTempCByIndex(0);

  // print out all params for validation by the raspi
  Serial.print("version: ");
  Serial.print(CODEBASE_VERSION);
  Serial.print("; target: ");
  Serial.print(TARGET_TEMPERATURE);
  Serial.print("; allowed deviation: ");
  Serial.print(ALLOWED_TEMPERATURE_DEVIATION);
  Serial.print("; measured: ");
  Serial.print(measured_temperature);
  Serial.println(";");

  // three thresholds from the two parameters (see Moritz' master's thesis)
  if(measured_temperature < TARGET_TEMPERATURE - ALLOWED_TEMPERATURE_DEVIATION){
    digitalWrite(HEATER,HIGH);
  }
  if(measured_temperature > TARGET_TEMPERATURE){
    digitalWrite(HEATER,LOW);
  }
  if(measured_temperature > TARGET_TEMPERATURE + ALLOWED_TEMPERATURE_DEVIATION){
    digitalWrite(FAN,HIGH);
  }
  if(measured_temperature < TARGET_TEMPERATURE){
    digitalWrite(FAN,LOW);
  }

  delay(5000);
}