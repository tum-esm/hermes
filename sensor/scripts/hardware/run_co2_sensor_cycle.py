import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, interfaces


config = interfaces.ConfigInterface.read()
co2_sensor = interfaces.CO2SensorInterface(
    config, logger=utils.Logger(config, origin="co2-sensor", print_to_console=True)
)

co2_sensor.get_current_concentration()
