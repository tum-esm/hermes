import os
import time
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
    logger.info(f"starting mainloop with process ID {os.getpid()}")

    try:
        mqtt_receiver = utils.ReceivingMQTTClient()
    except Exception as e:
        logger.error("could not start mqtt receiver")
        logger.exception(e)
        return

    try:
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception(e)

    # message archiving is always running, sending is optional
    if config.active_components.mqtt_data_sending:
        utils.SendingMQTTClient.init_sending_loop_process()
    utils.SendingMQTTClient.init_archiving_loop_process()

    # a single hardware interface that is only used by one procedure at a time
    # incremental backoff times on exceptions (15s, 1m, 5m, 20m)
    hardware_interface = hardware.HardwareInterface(config)
    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 60, 300, 1200]

    # system_check:   logging system statistics and reporting hardware/system errors
    # configuration:  updating the configuration/the software version on request
    # calibration:    using the two reference gas bottles to calibrate the CO2 sensor
    # measurements:   using the two reference gas bottles to calibrate the CO2 sensor

    system_check_prodecure = procedures.SystemCheckProcedure(config, hardware_interface)
    configuration_prodecure = procedures.ConfigurationProcedure(config)
    calibration_prodecure = procedures.CalibrationProcedure(config, hardware_interface)
    measurement_prodecure = procedures.MeasurementProcedure(config, hardware_interface)

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
            new_config_message = mqtt_receiver.get_config_message()
            if new_config_message is not None:
                # disconnect all hardware components to test new config
                hardware_interface.teardown()

                logger.info("running configuration procedure")
                configuration_prodecure.run(new_config_message)

                # reinit if update is unsuccessful
                hardware_interface.reinitialize(config)

            # TODO: what if the upgrade to the new pinned revision fails?
            # -> wait at least 20 minutes until trying to upgrade to the
            # same revision again?

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
            logger.exception(e, config=config)
            hardware_interface.perform_hard_reset()

            # -----------------------------------------------------------------
            # INCREMENTAL BACKOFF TIMES

            current_backoff_time = backoff_time_buckets[backoff_time_bucket_index]
            logger.error(f"waiting for {current_backoff_time} seconds", config=config)
            time.sleep(current_backoff_time)
            backoff_time_bucket_index = min(
                backoff_time_bucket_index + 1,
                len(backoff_time_buckets) - 1,
            )
