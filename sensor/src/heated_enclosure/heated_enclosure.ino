// pass variables from outside
#include "config.h"

// https://github.com/PaulStoffregen/OneWire
#include <OneWire.h>

// https://github.com/milesburton/Arduino-Temperature-Control-Library
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2  //Sensor DS18B20 am digitalen Pin 2
#define HEATER 4 //Control of heater relais
#define FAN 3 //Control of fan relais

OneWire oneWire(ONE_WIRE_BUS); //
DallasTemperature sensors(&oneWire); //Übergabe der OnewWire Referenz zum kommunizieren mit dem Sensor.

int sensorCount;
bool climate_state;
float measured_temperature;

void setup(void) { 
  Serial.begin(9600); //Starten der seriellen Kommunikation mit 9600 baud
  sensors.begin(); //Starten der Kommunikation mit dem Sensor
  sensorCount = sensors.getDS18Count(); //Lesen der Anzahl der angeschlossenen Temperatursensoren.
  pinMode(HEATER,OUTPUT);
  pinMode(FAN,OUTPUT);
  digitalWrite(HEATER,HIGH);
  digitalWrite(FAN,HIGH);
} 

void loop(void){ 
  // set both relais to LOW state
  if(sensorCount == 0){
    Serial.println("no temperature sensor");
  }
  //Es können mehr als 1 Temperatursensor am Datenbus angschlossen werden.
  //Anfordern der Temperaturwerte aller angeschlossenen Temperatursensoren.
  sensors.requestTemperatures(); 
  measured_temperature = sensors.getTempCByIndex(0);
  Serial.print("version: ");
  Serial.print(CODEBASE_VERSION);
  Serial.print("; target: ");
  Serial.print(TARGET_TEMPERATURE);
  Serial.print("; allowed deviation: ");
  Serial.print(ALLOWED_TEMPERATURE_DEVIATION);
  Serial.print("; measured: ");
  Serial.print(measured_temperature);
  Serial.println(";");

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