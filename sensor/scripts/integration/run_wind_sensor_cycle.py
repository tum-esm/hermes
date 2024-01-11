import json
import time
import os
import sys

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware

config = utils.ConfigInterface.read()
wind_sensor = hardware.WindSensorInterface(config)

for i in range(30):
    (
        current_measurement,
        current_device_status,
    ) = wind_sensor.get_current_sensor_measurement()
    print("current_measurement: ", end="")

    if current_measurement is not None:
        print(json.dumps(current_measurement.dict(), indent=4))
    else:
        print("null")

    print("current_device_status: ", end="")
    if current_device_status is not None:
        print(json.dumps(current_device_status.dict(), indent=4))
    else:
        print("null")

    time.sleep(2)

print("tearing down interface")
wind_sensor.teardown()
