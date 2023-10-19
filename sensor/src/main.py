import os
import signal
import time
from typing import Any, Optional
from src import custom_types, utils, hardware, procedures


def run() -> None:
    """Entry point for the measurement automation

    (e) Indicates possibility of an exception that blocks further execution

    INIT

    - State Interface
    - Timeouts
    - MQTT Agent
    - Initialize Hardware Interface (e)
    - Initialise Config Procedure (e)
    - Initialise Procedures (e) (System Checks, Calibration, Measurement)

    RUN INFINITE MAIN LOOP
    - Procedure: System Check
    - Procedure: Calibration
    - Procedure: Measurements (CO2, Wind)
    - Check for configuration update
    """

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

    # check and provide valid state file
    utils.StateInterface.init()

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

    # Exponental backoff time
    ebo = utils.ExponentialBackOff()

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

    # -------------------------------------------------------------------------
    # initialize all hardware interfaces
    # tear down hardware on program termination

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
    # initialize procedures

    # initialize config procedure
    new_config_message: Optional[custom_types.MQTTConfigurationRequest] = None
    configuration_prodecure = procedures.ConfigurationProcedure(config)

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
            # CONFIGURATION

            utils.set_alarm(MAX_CONFIG_UPDATE_TIME, "config update")

            logger.info("checking for new config messages")
            new_config_message = procedures.MQTTAgent.get_config_message()

            if new_config_message is not None:
                # shut down hardware interface before config update
                # this allows the pytests to test the new config on local hardware
                try:
                    hardware_interface.teardown()
                except Exception as e:
                    logger.exception(
                        e,
                        "error in hardware-teardown before configuration procedure",
                        config=config,
                    )
                    exit(1)

                # run config update procedure
                logger.info("running configuration procedure", config=config)
                try:
                    configuration_prodecure.run(new_config_message)
                    # -> Exit, Restarts via Cron Job to load new config
                except:
                    # reinitialize hardware if configuration failed
                    hardware_interface.reinitialize(config)

            # -----------------------------------------------------------------

            logger.info("finished mainloop iteration")
            backoff_time_bucket_index = 0
            last_successful_mainloop_iteration_time = time.time()

        except procedures.MQTTAgent.CommunicationOutage as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # reboot if exception lasts longer than 24 hours
            if (time.time() - last_successful_mainloop_iteration_time) >= 86400:
                logger.info(
                    "rebooting because no successful MQTT connect for 24 hours",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                # check timer with exponential backoff
                if time.time() > ebo.next_try_timer():
                    ebo.set_next_timer()
                    # try to establish mqtt connection
                    logger.info(
                        f"restarting messaging agent",
                        config=config,
                    )
                    procedures.MQTTAgent.deinit()
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

        except Exception as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # reboot if exception lasts longer than 12 hours
            if (time.time() - last_successful_mainloop_iteration_time) >= 86400:
                logger.info(
                    "rebooting because no successful mainloop iteration for 24 hours",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                # check timer with exponential backoff
                if time.time() > ebo.next_try_timer():
                    ebo.set_next_timer()
                    # reinitialize all hardware interfaces
                    logger.info("performing hard reset", config=config)
                    hardware_interface.teardown()
                    hardware_interface.reinitialize(config)
                    logger.info("hard reset was successful", config=config)

            except Exception as e:
                logger.exception(
                    e,
                    label="exception during hard reset of hardware",
                    config=config,
                )
                exit(1)
