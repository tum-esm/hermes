import os
import time
from src import interfaces, procedures, utils


def run() -> None:
    """entry point of the mainloop running continuously on the sensor node"""

    config = interfaces.ConfigInterface.read()
    logger = utils.Logger(config, origin="main")
    logger.info(f"starting mainloop with process ID {os.getpid()}")

    # mqtt_interface = interfaces.MQTTInterface(config)
    system_check_prodecure = procedures.SystemCheckProcedure()
    # TODO: init configuration-procedure instance
    # TODO: init calibration-procedure instance
    # TODO: init measurement-procedure instance

    while True:
        logger.info("starting mainloop iteration")

        logger.info("running system checks")
        system_check_prodecure.run(config)

        """
        1. read mqtt messages
        2. if config update request in messages:
            * run configuration procedure
            * config = interfaces.ConfigInterface.read()
            * logger = utils.Logger(config, origin="main")
            * continue
        3. if calibration is due:
            * do calbration
            * continue
        4. run measurement procedure
        """

        logger.info("finished mainloop iteration")

        # not needed anymore once all procedures have been implemented
        time.sleep(10)
