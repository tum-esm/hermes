# Following the thingsboard documentation: https://thingsboard.io/docs/user-guide/device-provisioning/?mqttprovisioning=without
# This script is used to provision a device in thingsboard in case the device is not already provisioned.
import os
import time

from src import procedures
from src import utils, custom_types

logger = utils.Logger(origin="thingsboard_provisioning", print_to_console=os.environ.get("HERMES_MODE") == "simulate")
message_queue = utils.MessageQueue()


def thingsboard_provisioning_procedure(config: custom_types.Config):
    if os.environ.get("HERMES_THINGSBOARD_ACCESS_TOKEN") is not None:
        logger.info("Found thingsboard access token!", config=config)
        return

    logger.info("Provisioning device in thingsboard...", config=config)
    if os.environ.get("HERMES_THINGSBOARD_PROVISION_DEVICE_KEY") is None:
        logger.error("No device provisioning key found for provisioning in thingsboard!")
        return
    if os.environ.get("HERMES_THINGSBOARD_PROVISION_DEVICE_SECRET") is None:
        logger.error("No device provisioning secret found for provisioning in thingsboard!")
        return
    if os.environ.get("HERMES_DEVICE_NAME") is None:
        logger.error("No device name found for provisioning in thingsboard!")
        return

    logger.info("Waiting for thingsboard provisioning...", config=config)
    for i in range(20):
        if procedures.MQTTAgent.communication_loop_process is not None:
            time.sleep(1)
            try:
                # call check_errors to update procedures.MQTTAgent.communication_loop_process
                procedures.MQTTAgent.check_errors()
            except Exception:
                # catch exceptions to exit gracefully instead
                pass
        else:
            logger.info("MQTT-process has quit - exiting....", config=config)
            time.sleep(3)
            exit(0)

    logger.error("Failed to provision device in thingsboard!", config=config)
    raise TimeoutError("Failed to provision device in thingsboard!")
