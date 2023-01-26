import os

import pytest
from ..pytest_fixtures import mqtt_client_environment, log_files
from ..pytest_utils import wait_for_condition
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils


@pytest.mark.ci
def test_mqtt_receiving(mqtt_client_environment: None, log_files: None) -> None:
    mqtt_client = utils.mqtt_connection.MQTTConnection.get_client()
    mqtt_config = utils.mqtt_connection.MQTTConnection.get_config()

    # testing whether config variables have been loaded correctly
    assert mqtt_config.station_identifier == utils.get_hostname()
    assert mqtt_config.mqtt_base_topic == os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"]

    # test connection and message sending
    assert mqtt_client.is_connected()
    message_info = mqtt_client.publish(topic="some", payload="hello", qos=1)
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )
