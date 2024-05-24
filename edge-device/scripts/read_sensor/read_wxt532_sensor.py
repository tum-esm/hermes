import time
from src import utils, hardware

config = utils.ConfigInterface.read()
wind_sensor = hardware.WindSensorInterface(config, testing=True)

while True:
    try:
        print(wind_sensor.get_current_sensor_measurement())
        time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        wind_sensor.teardown()
