import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, interfaces


config = interfaces.ConfigInterface.read()
co2_sensor = interfaces.CO2SensorInterface(
    config, logger=utils.Logger(config, origin="co2-sensor", print_to_console=True)
)

for i in range(10):
    print("send")
    print(co2_sensor.get_current_concentration())
    time.sleep(2)
