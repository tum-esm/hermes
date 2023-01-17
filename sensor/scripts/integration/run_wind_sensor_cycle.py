import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware


config = hardware.ConfigInterface.read()
wind_sensor = hardware.WindSensorInterface(
    config, logger=utils.Logger(config, origin="co2-sensor", print_to_console=True)
)

for i in range(30):
    print("update")
    current_values = wind_sensor.get_current_values()
    print(current_values)
    time.sleep(2)

print("tearing down interface")
wind_sensor.teardown()
