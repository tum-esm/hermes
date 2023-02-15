import os
import signal
import time
from typing import Any
from src import utils, hardware, procedures


class ExitOnHardwareTeardownFail(Exception):
    """raised when hardware.teardown() fails when called before the config
    procedure should run. A fail in this location would mean that the sensor
    is not able to upgrade until a reboot happens"""


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
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception()
        raise e

    # incremental backoff times on exceptions (15s, 1m, 5m, 20m)
    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 60, 300, 1200]

    # -------------------------------------------------------------------------
    # initialize mqtt receiver, archiver, and sender (sending is optional)

    try:
        procedures.MessagingAgent.init(config)
    except Exception as e:
        logger.error("could not start messaging agent")
        logger.exception()
        raise e

    procedures.MessagingAgent.check_errors()

    # wait until retained messages arrive
    time.sleep(2)

    # -------------------------------------------------------------------------
    # initialize config procedure and check for new configurations
    # before doing any hardware stuff

    configuration_prodecure = procedures.ConfigurationProcedure(config)
    logger.info("checking for new config messages")
    new_config_message = procedures.MessagingAgent.get_config_message()
    if new_config_message is None:
        logger.warning("initial config message not received", config=config)
    else:
        # exiting inside the procedure if successful
        logger.info("running configuration procedure")
        configuration_prodecure.run(new_config_message)

    # -------------------------------------------------------------------------
    # initialize a single hardware interface that is only used by one
    # procedure at a time; tear down hardware on program termination

    try:
        hardware_interface = hardware.HardwareInterface(config)
    except Exception as e:
        logger.error("could not initialize hardware interface", config=config)
        logger.exception(config=config)
        raise e

    # tear down hardware on program termination
    def graceful_teardown(*args: Any) -> None:
        logger.info("starting graceful shutdown")
        hardware_interface.teardown()
        logger.info("finished graceful shutdown")
        exit(0)

    signal.signal(signal.SIGINT, graceful_teardown)
    signal.signal(signal.SIGTERM, graceful_teardown)

    # -------------------------------------------------------------------------
    # initialize procedures interacting with hardware
    # system_check:   logging system statistics and reporting hardware/system errors
    # calibration:    using the two reference gas bottles to calibrate the CO2 sensor
    # measurements:   do regular measurements for x minutes

    try:
        system_check_prodecure = procedures.SystemCheckProcedure(
            config, hardware_interface
        )
        calibration_prodecure = procedures.CalibrationProcedure(
            config, hardware_interface
        )
        measurement_prodecure = procedures.MeasurementProcedure(
            config, hardware_interface
        )
    except Exception as e:
        logger.error("could not initialize procedures", config=config)
        logger.exception(config=config)
        raise e

    # -------------------------------------------------------------------------
    # infinite mainloop

    while True:
        try:
            logger.info("starting mainloop iteration")

            # -----------------------------------------------------------------
            # CONFIGURATION

            logger.info("checking for new config messages")
            new_config_message = procedures.MessagingAgent.get_config_message()
            if new_config_message is not None:

                try:
                    hardware_interface.teardown()
                except Exception as e:
                    logger.exception(config=config)
                    raise ExitOnHardwareTeardownFail()

                # stopping this script inside the procedure if successful
                logger.info("running configuration procedure")
                configuration_prodecure.run(new_config_message)

                hardware_interface.reinitialize(config)

            # -----------------------------------------------------------------
            # SYSTEM CHECKS

            logger.info("running system checks")
            system_check_prodecure.run()

            # -----------------------------------------------------------------
            # CALIBRATION

            if config.active_components.calibration_procedures:
                if calibration_prodecure.is_due():
                    logger.info("running calibration procedure", config=config)
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

        except procedures.ConfigurationProcedure.ExitOnUpdateSuccess:
            logger.info(
                "shutting down mainloop due to successful update",
                config=config,
            )
            exit(0)

        except ExitOnHardwareTeardownFail:
            logger.error(
                "shutting down mainloop due to failed "
                + "hardware.teardown() before config update",
                config=config,
            )
            exit(-1)

        except Exception as e1:
            try:
                hardware_interface.perform_hard_reset()
            except Exception as e2:
                logger.error(
                    "exception in mainloop and during hard reset of hardware",
                    config=config,
                )
                logger.exception(config=config)
                raise e2

            # send exception via MQTT
            current_backoff_time = backoff_time_buckets[backoff_time_bucket_index]
            logger.error(
                f"exception in mainloop, hard reset successful,"
                + f" waiting for {current_backoff_time} seconds",
                config=config,
            )
            logger.exception(config=config)

            # wait until starting up again
            time.sleep(current_backoff_time)
            backoff_time_bucket_index = min(
                backoff_time_bucket_index + 1,
                len(backoff_time_buckets) - 1,
            )
