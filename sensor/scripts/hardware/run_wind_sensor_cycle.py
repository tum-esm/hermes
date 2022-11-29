import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, interfaces


config = interfaces.ConfigInterface.read()
wind_sensor = interfaces.WindSensorInterface(
    config, logger=utils.Logger(config, origin="co2-sensor", print_to_console=True)
)

for i in range(30):
    print("update")
    wind_sensor.get_current_values()
    time.sleep(2)

print("tearing down interface")
wind_sensor.teardown()
