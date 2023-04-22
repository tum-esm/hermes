import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware

config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)
pump.set_desired_pump_speed(unit="rps", value=30)

valves = hardware.ValveInterface(config)
valve_no = int(input("Enter valve number: "))
assert valve_no in [1, 2, 3, 4]
valves.set_active_input(valve_no)

co2_sensor = hardware.CO2SensorInterface(config)

while True:
    print(co2_sensor.get_current_concentration())
