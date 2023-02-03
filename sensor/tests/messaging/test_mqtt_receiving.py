import json
import time
import pytest
from os.path import dirname, abspath, join
import sys
import os

from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_data_files,
    log_files,
    sample_config,
)
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
CONFIG_PATH = join(PROJECT_DIR, "config", "config.json")
sys.path.append(PROJECT_DIR)

from src import custom_types, utils, procedures


@pytest.mark.config_update
@pytest.mark.ci
def test_mqtt_receiving(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:

    # -------------------------------------------------------------------------
    # 1. PUBLISH RETAINED CONFIG MESSAGE

    mqtt_connection = utils.MQTTConnection()
    mqtt_config = mqtt_connection.config
    mqtt_client = mqtt_connection.client

    config_topic = (
        f"{mqtt_config.mqtt_base_topic}configurations/{mqtt_config.station_identifier}"
    )
    print(f"config_topic = {config_topic}")
    message = custom_types.MQTTConfigurationRequest(
        revision=1, configuration={"version": "0.1.0", "other_params": 30}
    ).dict()
    message_info = mqtt_client.publish(
        topic=config_topic,
        payload=json.dumps(message),
        qos=1,
        retain=True,
    )
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )
    mqtt_connection.teardown()
    assert not mqtt_client.is_connected(), "mqtt client is still connected"

    time.sleep(1)

    # -------------------------------------------------------------------------
    # 2. RECEIVE RETAINED CONFIG MESSAGE ON MESSAGING AGENT STARTUP

    with open(CONFIG_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.active_components.mqtt_communication = True
    procedures.MessagingAgent.init(config)

    time.sleep(3)

    expect_log_lines(
        required_lines=[
            f"message-communication   - INFO          - subscribed to topic {config_topic}",
        ]
    )

    # TODO: expect retained config to be received
