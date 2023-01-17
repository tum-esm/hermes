import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware


config = hardware.ConfigInterface.read()
co2_sensor = hardware.CO2SensorInterface(
    config, logger=utils.Logger(config, origin="co2-sensor", print_to_console=True)
)

print("??: ", end="")
device_info = co2_sensor.get_device_info()
print(device_info)

print("corr: ", end="")
correction_info = co2_sensor.get_correction_info()
print(correction_info)

print("errs: ", end="")
co2_sensor.check_sensor_errors()  # will raise an exception on error

for i in range(10):
    print("send: ", end="")
    print(co2_sensor.get_current_concentration())
    time.sleep(2)

print("tearing down interface")
co2_sensor.teardown()
