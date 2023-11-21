import time
from src import utils, hardware


try:
    config = utils.ConfigInterface.read()
except Exception as e:
    raise e


wind_sensor = hardware.WindSensorInterface(config, testing=True)

while True:
    print(wind_sensor.get_current_device_status())
    time.sleep(1)
    print(wind_sensor.get_current_wind_measurement())
    time.sleep(1)
