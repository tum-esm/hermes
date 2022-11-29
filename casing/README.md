The casing around the sensor box has:
* a heater and a cooler which can each be on or off
* a temperature sensor

The goal of this system is to keep its inner temperature stable at a certain target temperature. However, the heater and cooler are not PWM controlled, hence we cannot use a PID controller but have to implement a simple control that does not toggle the heating component power too often.