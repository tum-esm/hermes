import time
from src import interfaces


def run() -> None:
    """
    entry point of the mainloop running continuously
    on the sensor node
    """
    while True:
        config = interfaces.ConfigInterface.read()
        print(f"Hello! config = {config}")
        interfaces.MQTTInterface(config)

        time.sleep(10)
