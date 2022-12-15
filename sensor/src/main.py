import os
import time
from src import procedures, utils


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
        mqtt_receiver = utils.ReceivingMQTTClient()
    except Exception as e:
        logger.error("could not start mqtt receiver")
        logger.exception(e)
        return

    # TODO: init configuration-procedure instance

    try:
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception(e)
        # TODO: fetch newest config from pinned topic messages
        #       and perform configuration procedure

    system_check_prodecure = procedures.SystemCheckProcedure(config)
    measurement_prodecure = procedures.MeasurementProcedure(config)

    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 60, 300, 900]

    while True:
        try:
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
            backoff_time_bucket_index = 0

        except Exception as e:
            logger.exception(e, config=config)

            # wait for an increasing amount of time
            current_backoff_time = backoff_time_buckets[backoff_time_bucket_index]
            logger.error(f"waiting for {current_backoff_time} seconds", config=config)
            time.sleep(current_backoff_time)
            if len(backoff_time_buckets) > (backoff_time_bucket_index + 1):
                backoff_time_bucket_index += 1
