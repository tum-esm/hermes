import time
import pytest
from os.path import dirname, abspath, join
import sys
import os

from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_data_files,
    messaging_agent_with_sending,
    log_files,
    sample_config,
)
from ..pytest_utils import expect_log_lines

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import custom_types, procedures


@pytest.mark.config_update
@pytest.mark.ci
def test_mqtt_receiving(messaging_agent_with_sending: None) -> None:
    mqtt_config = custom_types.MQTTConfig(
        station_identifier=os.environ.get("HERMES_MQTT_IDENTIFIER"),
        mqtt_url=os.environ.get("HERMES_MQTT_URL"),
        mqtt_port=os.environ.get("HERMES_MQTT_PORT"),
        mqtt_username=os.environ.get("HERMES_MQTT_USERNAME"),
        mqtt_password=os.environ.get("HERMES_MQTT_PASSWORD"),
        mqtt_base_topic=os.environ.get("HERMES_MQTT_BASE_TOPIC"),
    )
    config_topic = (
        f"{mqtt_config.mqtt_base_topic}configurations/{mqtt_config.station_identifier}"
    )
    print(f"config_topic = {config_topic}")

    assert procedures.MessagingAgent.get_config_message() is None
    time.sleep(1)

    expect_log_lines(
        required_lines=[
            f"message-communication   - INFO          - subscribed to topic {config_topic}",
        ]
    )
