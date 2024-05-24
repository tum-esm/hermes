import os
import sys
import time
from typing import Literal
from src import utils, hardware

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)


config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)
pump.set_desired_pump_speed(pwm_duty_cycle=0.15)

valves = hardware.ValveInterface(config)
valve_no: Literal[1, 2, 3, 4] = int(input("Enter valve number: "))  # type:ignore
assert valve_no in [1, 2, 3, 4]
valves.set_active_input(valve_no)

co2_sensor = hardware.CO2SensorInterface(config)
inlet_sht45 = hardware.SHT45SensorInterface(config)
inlet_bme280 = hardware.BME280SensorInterface(config, variant="air-inlet")
io_bme280 = hardware.BME280SensorInterface(config, variant="ioboard")

try:
    while True:
        print(co2_sensor.get_current_concentration())
        print(inlet_sht45.get_data())
        print(inlet_bme280.get_data())
        print(io_bme280.get_data())
        time.sleep(5)
except KeyboardInterrupt:
    print("\n 🚫 starting teardown")

co2_sensor.teardown()
inlet_bme280.teardown()
io_bme280.teardown()
pump.teardown()
valves.teardown()

print("✅ done")
