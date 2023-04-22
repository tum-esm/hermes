import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware


config = utils.ConfigInterface.read()
sht45 = hardware.SHT45SensorInterface(config)
bme280 = hardware.BME280SensorInterface(config, variant="air inlet")

while True:
    print("SHT45:", sht45.get_data())
    print("BME280:", bme280.get_data())
    print()
    time.sleep(1)
