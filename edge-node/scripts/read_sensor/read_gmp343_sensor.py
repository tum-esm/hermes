import time
from src import utils, hardware

config = utils.ConfigInterface.read()
co2_sensor = hardware.CO2SensorInterface(config, testing=True)

while True:
    try:
        print(co2_sensor.get_current_concentration())
        time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        co2_sensor.teardown()
