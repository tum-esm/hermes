import os
import signal
import time
from typing import Any
from src import utils, hardware, procedures


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
    logger.horizontal_line()
    logger.info(f"starting mainloop with process ID {os.getpid()}")

    try:
        mqtt_receiver = utils.ReceivingMQTTClient()
    except Exception as e:
        logger.error("could not start mqtt receiver")
        logger.exception(e)
        raise e

    try:
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception(e)
        raise e

    # message archiving is always running, sending is optional
    try:
        if config.active_components.mqtt_data_sending:
            utils.SendingMQTTClient.init_sending_loop_process()
        utils.SendingMQTTClient.init_archiving_loop_process()
    except Exception as e:
        logger.error("could not start mqtt sending/archiving loop")
        logger.exception(e)
        raise e

    # a single hardware interface that is only used by one procedure at a time
    try:
        hardware_interface = hardware.HardwareInterface(config)
    except Exception as e:
        logger.error("could not initialize hardware interfaces")
        logger.exception(e)
        raise e

    # incremental backoff times on exceptions (15s, 1m, 5m, 20m)
    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 60, 300, 1200]

    # tear down hardware on program termination
    def graceful_teardown(*args: Any) -> None:
        logger.info("starting graceful shutdown")
        hardware_interface.teardown()
        logger.info("finished graceful shutdown")
        exit(0)

    signal.signal(signal.SIGINT, graceful_teardown)
    signal.signal(signal.SIGTERM, graceful_teardown)

    # system_check:   logging system statistics and reporting hardware/system errors
    # configuration:  updating the configuration/the software version on request
    # calibration:    using the two reference gas bottles to calibrate the CO2 sensor
    # measurements:   do regular measurements for x minutes

    try:
        system_check_prodecure = procedures.SystemCheckProcedure(
            config, hardware_interface
        )
        configuration_prodecure = procedures.ConfigurationProcedure(config)
        calibration_prodecure = procedures.CalibrationProcedure(
            config, hardware_interface
        )
        measurement_prodecure = procedures.MeasurementProcedure(
            config, hardware_interface
        )
    except Exception as e:
        logger.error("could not initialize procedures")
        logger.exception(e)
        raise e

    while True:
        try:
            logger.info("starting mainloop iteration")

            # -----------------------------------------------------------------
            # SYSTEM CHECKS

            logger.info("running system checks")
            system_check_prodecure.run()

            # -----------------------------------------------------------------
            # CONFIGURATION

            logger.info("checking for new config messages")
            # TODO: get pinned config if revision is different
            # TODO: do not try an upgrade to a specific revision twice
            new_config_message = mqtt_receiver.get_config_message()
            if new_config_message is not None:
                # disconnect all hardware components to test new config
                hardware_interface.teardown()

                # stopping this script inside the procedure if successful
                logger.info("running configuration procedure")
                configuration_prodecure.run(new_config_message)

                # reinit if update is unsuccessful
                hardware_interface.reinitialize(config)

            # -----------------------------------------------------------------
            # CALIBRATION

            if config.active_components.calibration_procedures:
                if calibration_prodecure.is_due():
                    logger.info("running calibration procedure")
                    calibration_prodecure.run()
                else:
                    logger.info("calibration procedure is not due")
            else:
                logger.info("skipping calibration procedure due to config")

            # -----------------------------------------------------------------
            # MEASUREMENTS

            # if messages are empty, run regular measurements
            logger.info("running measurements")
            measurement_prodecure.run()

            # -----------------------------------------------------------------

            logger.info("finished mainloop iteration")
            backoff_time_bucket_index = 0

        except Exception as e:
            logger.error("exception in mainloop")
            logger.exception(e, config=config)
            try:
                hardware_interface.perform_hard_reset()

                # -----------------------------------------------------------------
                # INCREMENTAL BACKOFF TIMES

                current_backoff_time = backoff_time_buckets[backoff_time_bucket_index]
                logger.error(
                    f"waiting for {current_backoff_time} seconds", config=config
                )
                time.sleep(current_backoff_time)
                backoff_time_bucket_index = min(
                    backoff_time_bucket_index + 1,
                    len(backoff_time_buckets) - 1,
                )
            except Exception as e:
                logger.error("exception in repairing routine")
                logger.exception(e, config=config)
                raise e
