import os
import time
from src import custom_types, utils, hardware, procedures


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

    utils.SendingMQTTClient.init_sending_loop_process()

    try:
        config = utils.ConfigInterface.read()
    except Exception as e:
        logger.error("could not load local config.json")
        logger.exception(e)
        # TODO: fetch newest config from pinned topic messages
        #       and perform configuration procedure

    # a single hardware interface that is only used by one procedure at a time
    hardware_interface = hardware.HardwareInterface(config)

    # logging system statistics and reporting hardware/system errors
    system_check_prodecure = procedures.SystemCheckProcedure(config, hardware_interface)

    # updating the configuration/the software version on request
    configuration_prodecure = procedures.ConfigurationProcedure(config)

    # using the two reference gas bottles to calibrate the CO2 sensor
    calibration_prodecure = procedures.CalibrationProcedure(config, hardware_interface)

    # doing regular measurements
    measurement_prodecure = procedures.MeasurementProcedure(config, hardware_interface)

    backoff_time_bucket_index = 0
    backoff_time_buckets = [15, 60, 300, 900]

    while True:
        try:
            logger.info("starting mainloop iteration")

            logger.info("running system checks")
            system_check_prodecure.run()

            # TODO: read mqtt messages
            if time.time() < 0:
                # disconnect all hardware components to test new
                # config, possibly reinit if update is unsuccessful
                hardware_interface.teardown()
                configuration_prodecure.run(
                    custom_types.MQTTConfigurationRequest(
                        **{"revision": 1, "configuration": {"version": "0.2.0"}}
                    )
                )
                hardware_interface.reinit()

            if calibration_prodecure.is_due():
                calibration_prodecure.run()

            # if messages are empty, run regular measurements
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
