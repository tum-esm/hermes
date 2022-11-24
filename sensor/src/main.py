from src import interfaces


def run() -> None:
    """
    entry point of the mainloop running continuously
    on the sensor node
    """
    config = interfaces.ConfigInterface.read()
    mqtt_interface = interfaces.MQTTInterface(config)

    # TODO: init config-procedure-class
    # TODO: init calibration-procedure-class
    # TODO: init measurement-procedure-class

    while True:
        config = interfaces.ConfigInterface.read()

        """
        1. read mqtt messages
        2. if config update request in messages:
            * run configuration procedure
            * continue
        3. if calibration is due:
            * do calbration
            * continue
        4. run measurement procedure
        """
