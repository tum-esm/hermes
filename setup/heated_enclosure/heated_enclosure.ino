// pass variables from outside
#include "config.h"

// https://github.com/PaulStoffregen/OneWire
#include <OneWire.h>

// https://github.com/milesburton/Arduino-Temperature-Control-Library
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2 // sensor DS18B20 on digital pin 2
#define HEATER 3       // control of heater relais
#define FAN 4          // control of fan relais

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
float measured_temperature;

bool heater_is_on = false;
bool fan_is_on = false;

void setup(void)
{
  Serial.begin(9600);
  sensors.begin();

  pinMode(HEATER, OUTPUT);
  pinMode(FAN, OUTPUT);
}

void loop(void)
{
  if (sensors.getDS18Count() == 0)
  {
    // Serial.print("null");
    heater_is_on = false;
    fan_is_on = false;
  }
  else
  {
    // there can be more than one temperature sensor on the databus
    sensors.requestTemperatures();
    measured_temperature = sensors.getTempCByIndex(0);
    Serial.print(measured_temperature);
    Serial.print(" ");

    if (measured_temperature < (TARGET_TEMPERATURE - ALLOWED_TEMPERATURE_DEVIATION))
    {
      heater_is_on = true;
    }
    if (measured_temperature > TARGET_TEMPERATURE)
    {
      heater_is_on = false;
    }
    if (measured_temperature > (TARGET_TEMPERATURE + ALLOWED_TEMPERATURE_DEVIATION))
    {
      fan_is_on = true;
    }
    if (measured_temperature < TARGET_TEMPERATURE)
    {
      fan_is_on = false;
    }
    
  }

  digitalWrite(HEATER, heater_is_on ? LOW : HIGH);
  digitalWrite(FAN, fan_is_on ? LOW : HIGH);

  delay(5000);
}