import time
from src import utils, hardware

config = utils.ConfigInterface.read()
bme280 = hardware.BME280SensorInterface(config, variant="ioboard", testing=True)

while True:
    try:
        print(bme280.get_data())
        time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        bme280.teardown()
