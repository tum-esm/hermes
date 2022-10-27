import time
from src import interfaces


def run() -> None:
    """
    entry point of the mainloop running continuously
    on the sensor node
    """
    config = interfaces.ConfigInterface.read()
    mqtt_interface = interfaces.MQTTInterface(config)

    while True:
        config = interfaces.ConfigInterface.read()
        print(f"Hello! config = {config}")

        print(f"new messages: {mqtt_interface.get_messages()}")
        time.sleep(10)
