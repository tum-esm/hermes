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
    logger = utils.Logger(origin="main")
    logger.info(f"starting mainloop with process ID {os.getpid()}")

    try:
        mqtt_receiver = interfaces.ReceivingMQTTClient()
    except Exception as e:
        logger.error("could not start mqtt receiver")
        logger.exception(e)
        return

    # TODO: init configuration-procedure instance

    try:
        config = interfaces.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception(e)
        # TODO: fetch newest config from pinned topic messages
        #       and perform configuration procedure

    system_check_prodecure = procedures.SystemCheckProcedure(config)
    # TODO: init calibration-procedure instance
    measurement_prodecure = procedures.MeasurementProcedure(config)

    # TODO: add try-except logic around mainloop
    # TODO: send exceptions over mqtt as well
    # TODO: ad incremental backoff time

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
