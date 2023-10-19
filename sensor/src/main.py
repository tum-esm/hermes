import os
import signal
import time
from typing import Any, Optional
from src import custom_types, utils, hardware, procedures


class ExitOnHardwareTeardownFail(Exception):
    """raised when hardware.teardown() fails when called before the config
    procedure should run. A fail in this location would mean that the sensor
    is not able to upgrade until a reboot happens"""


def run() -> None:
    """Entry point of the mainloop running continuously on the sensor node

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
    # TODO: Update the run description with more details

    logger = utils.Logger(origin="main")
    logger.horizontal_line()

    try:
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.exception(e, label="could not load local config.json")
        raise e

    logger.info(
        f"started new automation process with PID {os.getpid()}",
        config=config,
    )

    # -------------------------------------------------------------------------
    # create state file if it does not exist yet, add upgrade time if missing

    utils.StateInterface.init()

    # -------------------------------------------------------------------------
    # define timeouts for parts of the automation

    MAX_SETUP_TIME = 180
    MAX_CONFIG_UPDATE_TIME = 1200
    MAX_SYSTEM_CHECK_TIME = 180
    MAX_CALIBRATION_TIME = (
        len(config.calibration.gases) + 1
    ) * config.calibration.timing.seconds_per_gas_bottle + 180
    MAX_MEASUREMENT_TIME = (
        config.measurement.timing.seconds_per_measurement_interval + 180
    )
    utils.set_alarm(MAX_SETUP_TIME, "setup")

    # -------------------------------------------------------------------------
    # define incremental backoff mechanism

    # will be used for rebooting when errors persist for more than 24 hours
    last_successful_mainloop_iteration_time = time.time()

    # incremental backoff times on exceptions (15s, 30s, 1m, 2m, 4m, 8m)
    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 30, 60, 120, 240, 480]

    def wait_during_repair() -> int:
        """Wait for the current backoff time and increase backoff time
        bucket index. Log the waiting time. Return the new backoff time
        bucket index."""
        current_backoff_time = backoff_time_buckets[backoff_time_bucket_index]
        logger.info(
            f"waiting for {current_backoff_time} seconds",
            config=config,
        )
        time.sleep(current_backoff_time)
        return min(
            backoff_time_bucket_index + 1,
            len(backoff_time_buckets) - 1,
        )

    # -------------------------------------------------------------------------
    # initialize mqtt receiver, archiver, and sender (sending is optional)

    try:
        procedures.MQTTAgent.init(config)
    except Exception as e:
        logger.exception(
            e,
            label="could not start messaging agent",
            config=config,
        )
        # at this point the automation can't be started without internet connection
        # or available broker
        # TODO: fix this
        raise e

    # -------------------------------------------------------------------------
    # initialize config procedure

    new_config_message: Optional[custom_types.MQTTConfigurationRequest] = None
    configuration_prodecure = procedures.ConfigurationProcedure(config)

    # -------------------------------------------------------------------------
    # initialize a single hardware interface that is only used by one
    # procedure at a time; tear down hardware on program termination

    logger.info("initializing hardware interfaces", config=config)

    try:
        hardware_interface = hardware.HardwareInterface(config)
    except Exception as e:
        logger.exception(
            e, label="could not initialize hardware interface", config=config
        )
        raise e

    # tear down hardware on program termination
    def _graceful_teardown(*args: Any) -> None:
        utils.set_alarm(10, "graceful teardown")

        logger.info("starting graceful teardown")
        hardware_interface.teardown()
        logger.info("finished graceful teardown")
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    logger.info("established graceful teardown hook")

    # -------------------------------------------------------------------------
    # initialize procedures interacting with hardware
    # system_check:   logging system statistics and reporting hardware/system errors
    # calibration:    using the two reference gas bottles to calibrate the CO2 sensor
    # measurements:   do regular measurements for x minutes

    logger.info("initializing procedures", config=config)

    try:
        system_check_prodecure = procedures.SystemCheckProcedure(
            config, hardware_interface
        )
        calibration_prodecure = procedures.CalibrationProcedure(
            config, hardware_interface
        )
        wind_measurement_prodecure = procedures.WindMeasurementProcedure(
            config, hardware_interface
        )
        CO2_measurement_prodecure = procedures.CO2MeasurementProcedure(
            config, hardware_interface
        )
    except Exception as e:
        logger.exception(e, label="could not initialize procedures", config=config)
        raise e

    # -------------------------------------------------------------------------
    # infinite mainloop

    logger.info("successfully finished setup, starting mainloop", config=config)

    while True:
        try:
            logger.info("starting mainloop iteration")

            # -----------------------------------------------------------------
            # CONFIGURATION

            utils.set_alarm(MAX_CONFIG_UPDATE_TIME, "config update")

            logger.info("checking for new config messages")
            new_config_message = procedures.MQTTAgent.get_config_message()
            if new_config_message is not None:
                try:
                    hardware_interface.teardown()
                except Exception as e:
                    logger.exception(
                        e,
                        "error in hardware-teardown before configuration procedure",
                        config=config,
                    )
                    raise ExitOnHardwareTeardownFail()

                # stopping this script inside the procedure if successful
                logger.info("running configuration procedure", config=config)
                configuration_prodecure.run(new_config_message)
                # Either raises an exception here if configuration was successful
                # Shuts down current run and waits for restart via Cron Job
                # -> Exit

                # Or reinitialized hardware if configuration failed (no exception was raised)
                hardware_interface.reinitialize(config)

            # -----------------------------------------------------------------
            # SYSTEM CHECKS

            utils.set_alarm(MAX_SYSTEM_CHECK_TIME, "system check")

            logger.info("running system checks")
            system_check_prodecure.run()

            # -----------------------------------------------------------------
            # CALIBRATION

            utils.set_alarm(MAX_CALIBRATION_TIME, "calibration")

            if config.active_components.run_calibration_procedures:
                if calibration_prodecure.is_due():
                    logger.info("running calibration procedure", config=config)
                    calibration_prodecure.run()
                else:
                    logger.info("calibration procedure is not due")
            else:
                logger.info("skipping calibration procedure due to config")

            # -----------------------------------------------------------------
            # MEASUREMENTS

            utils.set_alarm(MAX_MEASUREMENT_TIME, "measurement")

            # if messages are empty, run regular measurements
            logger.info("running measurements")
            wind_measurement_prodecure.run()
            CO2_measurement_prodecure.run()

            # -----------------------------------------------------------------

            logger.info("finished mainloop iteration")
            backoff_time_bucket_index = 0
            last_successful_mainloop_iteration_time = time.time()

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
            exit(1)

        except procedures.MQTTAgent.CommunicationOutage as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # reboot if exception lasts longer than 12 hours
            if (time.time() - last_successful_mainloop_iteration_time) >= 43200:
                logger.info(
                    "rebooting because no successful mainloop iteration for 12 hours",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                logger.info(
                    f"restarting messaging agent",
                    config=config,
                )
                procedures.MQTTAgent.deinit()
                # the back_off_time_bucket leads to measurement downtime
                backoff_time_bucket_index = wait_during_repair()
                procedures.MQTTAgent.init(config)
                logger.info(
                    f"successfully restarted messaging agent",
                    config=config,
                )
            except Exception as e:
                logger.exception(
                    e,
                    label="failed to restart messaging agent",
                    config=config,
                )
                raise e

        except Exception as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # reboot if exception lasts longer than 12 hours
            if (time.time() - last_successful_mainloop_iteration_time) >= 43200:
                logger.info(
                    "rebooting because no successful mainloop iteration for 12 hours",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                logger.info("performing hard reset", config=config)
                hardware_interface.teardown()
                backoff_time_bucket_index = wait_during_repair()
                hardware_interface.reinitialize(config)
                logger.info("hard reset was successful", config=config)

            except Exception as e:
                logger.exception(
                    e,
                    label="exception during hard reset of hardware",
                    config=config,
                )
                raise e
