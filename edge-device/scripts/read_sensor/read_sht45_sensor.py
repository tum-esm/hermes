import time
from src import utils, hardware

config = utils.ConfigInterface.read()
sht45 = hardware.SHT45SensorInterface(config, testing=True)

while True:
    try:
        print(sht45.get_data())
        time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        pass
