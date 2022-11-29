import time
from src import interfaces, procedures


def run() -> None:
    """
    entry point of the mainloop running continuously
    on the sensor node
    """
    config = interfaces.ConfigInterface.read()
    # mqtt_interface = interfaces.MQTTInterface(config)

    system_check_prodecure = procedures.SystemCheckProcedure()

    # TODO: init configuration-procedure instance
    # TODO: init calibration-procedure instance
    # TODO: init measurement-procedure instance

    while True:
        config = interfaces.ConfigInterface.read()
        system_check_prodecure.run(config)

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

        # not needed anymore once all procedures have been implemented
        time.sleep(10)
