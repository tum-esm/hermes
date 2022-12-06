import os
import time
from src import interfaces, procedures, utils


def run() -> None:
    """
    entry point of the mainloop running continuously on the sensor node

    0. system checks
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

    # TODO: routine that loads the environment MQTT parameters

    # TODO: if local config does not exist: fetch newest config
    #       from pinned topic messages and perform update

    # TODO: do not use station name by logger

    config = interfaces.ConfigInterface.read()
    logger = utils.Logger(config, origin="main")
    logger.info(f"starting mainloop with process ID {os.getpid()}")

    # TODO: mqtt_interface = interfaces.ReceivingMQTTClient(config)
    system_check_prodecure = procedures.SystemCheckProcedure(config)
    # TODO: init configuration-procedure instance
    # TODO: init calibration-procedure instance
    measurement_prodecure = procedures.MeasurementProcedure(config)

    while True:
        logger.info("starting mainloop iteration")

        logger.info("running system checks")
        system_check_prodecure.run()

        # TODO: read mqtt messages
        # TODO: optionally call configuration routine -> triggers a restart if config is accepted
        # TODO: optionally call calibration routing
        # TODO: run teardown of other procedures before configuration/calibration

        # TODO: if messages are empty, run, skip otherwise
        logger.info("running measurements")
        measurement_prodecure.run()

        logger.info("finished mainloop iteration")

        # not needed anymore once all procedures have been implemented
        time.sleep(10)
