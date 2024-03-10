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
    - Initialize Config Procedure (e)
    - Initialize Procedures (e) (System Checks, Calibration, Measurement)

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
        f"Started new automation process with SW version {config.version} and PID {os.getpid()}.",
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
        (len(config.calibration.gas_cylinders) + 1)
        * config.calibration.sampling_per_cylinder_seconds
        + 300  # flush time
        + 180  # extra time
    )
    MAX_MEASUREMENT_TIME = config.measurement.procedure_seconds + 180  # extra time
    utils.set_alarm(MAX_SETUP_TIME, "setup")

    # Exponential backoff time
    ebo = utils.ExponentialBackOff()

    # -------------------------------------------------------------------------
    # initialize mqtt receiver, archiver, and sender (sending is optional)

    try:
        procedures.MQTTAgent.init(config)
    except Exception as e:
        logger.exception(
            e,
            label="Could not start messaging agent.",
            config=config,
        )

    # -------------------------------------------------------------------------
    # initialize all hardware interfaces
    # tear down hardware on program termination

    logger.info("Initializing hardware interfaces.", config=config)

    try:
        hardware_interface = hardware.HardwareInterface(config)
    except Exception as e:
        logger.exception(
            e, label="Could not initialize hardware interface.", config=config
        )
        raise e

    # tear down hardware on program termination
    def _graceful_teardown(*args: Any) -> None:
        utils.set_alarm(10, "graceful teardown")

        logger.info("Starting graceful teardown.")
        hardware_interface.teardown()
        logger.info("Finished graceful teardown.")
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    logger.info("Established graceful teardown hook.")

    # -------------------------------------------------------------------------
    # initialize procedures

    # initialize config procedure
    new_config_message: Optional[custom_types.MQTTConfigurationRequest] = None
    configuration_procedure = procedures.ConfigurationProcedure(config)

    # initialize procedures interacting with hardware
    # system_check:   logging system statistics and reporting hardware/system errors
    # calibration:    using the two reference gas bottles to calibrate the CO2 sensor
    # measurements:   do regular measurements for x minutes

    logger.info("Initializing procedures.", config=config)

    try:
        system_check_procedure = procedures.SystemCheckProcedure(
            config, hardware_interface
        )
        calibration_procedure = procedures.CalibrationProcedure(
            config, hardware_interface
        )
        wind_measurement_procedure = procedures.WindMeasurementProcedure(
            config, hardware_interface
        )
        co2_measurement_procedure = procedures.CO2MeasurementProcedure(
            config, hardware_interface
        )
    except Exception as e:
        logger.exception(e, label="could not initialize procedures", config=config)
        raise e

    # -------------------------------------------------------------------------
    # infinite mainloop

    logger.info("Successfully finished setup, starting mainloop.", config=config)

    while True:
        try:
            logger.info("Starting mainloop iteration.")

            # -----------------------------------------------------------------
            # SYSTEM CHECKS

            utils.set_alarm(MAX_SYSTEM_CHECK_TIME, "system check")

            logger.info("Running system checks.")
            system_check_procedure.run()

            # -----------------------------------------------------------------
            # CALIBRATION

            utils.set_alarm(MAX_CALIBRATION_TIME, "calibration")

            if config.active_components.run_calibration_procedures:
                if calibration_procedure.is_due():
                    logger.info("Running calibration procedure.", config=config)
                    calibration_procedure.run()
                else:
                    logger.info("Calibration procedure is not due.")
            else:
                logger.info("Skipping calibration procedure due to config.")

            # -----------------------------------------------------------------
            # MEASUREMENTS

            utils.set_alarm(MAX_MEASUREMENT_TIME, "measurement")

            # if messages are empty, run regular measurements
            logger.info("Running measurements.")
            wind_measurement_procedure.run()
            co2_measurement_procedure.run()

            # -----------------------------------------------------------------
            # CONFIGURATION

            utils.set_alarm(MAX_CONFIG_UPDATE_TIME, "config update")

            logger.info("Checking for new config messages.")
            new_config_message = procedures.MQTTAgent.get_config_message()

            if new_config_message is not None:
                # run config update procedure
                logger.info("Running configuration procedure.", config=config)
                try:
                    configuration_procedure.run(new_config_message)
                    # -> Exit, Restarts via Cron Job to load new config
                except Exception:
                    # reinitialize hardware if configuration failed
                    logger.info(
                        "Exception during configuration procedure.", config=config
                    )
                    hardware_interface.reinitialize(config)

            # -----------------------------------------------------------------
            # MQTT Agent Checks

            if config.active_components.send_messages_over_mqtt:
                procedures.MQTTAgent.check_errors()

            # -----------------------------------------------------------------

            logger.info("Finished mainloop iteration.")
            last_successful_mainloop_iteration_time = time.time()

            # update state config
            state = utils.StateInterface.read()
            if state.offline_since:
                state.offline_since = None
                # utils.StateInterface.write(state)

        except procedures.MQTTAgent.CommunicationOutage as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # update state config if first raise
            state = utils.StateInterface.read()
            if not state.offline_since:
                state.offline_since = time.time()
                utils.StateInterface.write(state)

            # reboot if exception lasts longer than 24 hours
            if (time.time() - state.offline_since) >= 86400:
                logger.info(
                    "Rebooting because no successful MQTT connect for 24 hours.",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                # check timer with exponential backoff
                if time.time() > ebo.next_try_timer():
                    ebo.set_next_timer()
                    # try to establish mqtt connection
                    logger.info(
                        f"Restarting messaging agent.",
                        config=config,
                    )
                    procedures.MQTTAgent.deinit()
                    procedures.MQTTAgent.init(config)
                    logger.info(
                        f"Successfully restarted messaging agent.",
                        config=config,
                    )
            except Exception as e:
                logger.exception(
                    e,
                    label="Failed to restart messaging agent.",
                    config=config,
                )

        except Exception as e:
            logger.exception(e, label="exception in mainloop", config=config)

            # cancel the alarm for too long mainloops
            signal.alarm(0)

            # reboot if exception lasts longer than 12 hours
            if (time.time() - last_successful_mainloop_iteration_time) >= 86400:
                logger.info(
                    "Rebooting because no successful mainloop iteration for 24 hours.",
                    config=config,
                )
                os.system("sudo reboot")

            try:
                # check timer with exponential backoff
                if time.time() > ebo.next_try_timer():
                    ebo.set_next_timer()
                    # reinitialize all hardware interfaces
                    logger.info("Performing hardware reset.", config=config)
                    hardware_interface.teardown()
                    hardware_interface.reinitialize(config)
                    logger.info("Hardware reset was successful.", config=config)

            except Exception as e:
                logger.exception(
                    e,
                    label="exception during hard reset of hardware",
                    config=config,
                )
                exit(1)
