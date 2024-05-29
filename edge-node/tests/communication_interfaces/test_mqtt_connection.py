import os
import pytest
from ..pytest_utils import wait_for_condition
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_mqtt_connection(mqtt_client_environment: None) -> None:
    mqtt_connection = utils.MQTTConnection()
    mqtt_config = mqtt_connection.config
    mqtt_client = mqtt_connection.client

    # testing setup
    assert mqtt_config.station_identifier == os.environ["HERMES_MQTT_IDENTIFIER"]
    assert mqtt_config.mqtt_base_topic == os.environ["HERMES_MQTT_BASE_TOPIC"]
    assert mqtt_client.is_connected(), "mqtt client is not connected"

    # test message sending
    message_info = mqtt_client.publish(topic="some", payload="hello", qos=1)
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )

    mqtt_connection.teardown()
    assert not mqtt_client.is_connected(), "mqtt client is still connected"
