import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


config = interfaces.ConfigInterface.read()
co2_sensor = interfaces.CO2SensorInterface(config)

co2_sensor.start_polling_measurements()

for i in range(3):
    time.sleep(2)
    print(co2_sensor.get_latest_measurements())

co2_sensor.stop_polling_measurements()
