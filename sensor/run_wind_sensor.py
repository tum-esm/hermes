import os
import signal
import time
from typing import Any, Optional
from src import custom_types, utils, hardware, procedures


try:
    config = utils.ConfigInterface.read()
except Exception as e:
    raise e
    
    
wind_sensor = hardware.WindSensorInterface(config, testing=True)

while(True):
    print(wind_sensor.get_current_device_status())
    time.sleep(1)
    print(wind_sensor.get_current_wind_measurement())
    time.sleep(1)