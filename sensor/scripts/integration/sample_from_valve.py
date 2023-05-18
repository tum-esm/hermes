import os
import sys
from typing import Literal

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware

config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)
pump.set_desired_pump_speed(unit="rps", value=30)

valves = hardware.ValveInterface(config)
valve_no: Literal[1, 2, 3, 4] = int(input("Enter valve number: "))  # type:ignore
assert valve_no in [1, 2, 3, 4]
valves.set_active_input(valve_no)

co2_sensor = hardware.CO2SensorInterface(config)
air_inlet_bme280_sensor = hardware.BME280SensorInterface(config, variant="air-inlet")
air_inlet_sht45_sensor = hardware.SHT45SensorInterface(config)
mainboard_bme280_sensor = hardware.BME280SensorInterface(config, variant="mainboard")

try:
    while True:
        print(co2_sensor.get_current_concentration())
        print(air_inlet_bme280_sensor.get_data())
        print(air_inlet_sht45_sensor.get_data())
        print(mainboard_bme280_sensor.get_data())
        print()
except KeyboardInterrupt:
    print("\n 🚫 starting teardown")

co2_sensor.teardown()
pump.teardown()
valves.teardown()

print("✅ done")

# soll: 800, filtered: 734.2
# soll: 400±, filtered: 376
# soll: outside, filterd: 15
