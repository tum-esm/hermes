import os

import pytest
from fixtures import mqtt_client_environment
from utils import wait_for_condition
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils


@pytest.mark.ci
def test_mqtt_receiving(mqtt_client_environment) -> None:
    mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()

    # testing whether config variables have been loaded correctly
    assert (
        mqtt_config.station_identifier
        == os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"]
    )
    assert mqtt_config.mqtt_base_topic == os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"]

    message_info = mqtt_client.publish(topic="some", payload="hello", qos=1)
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )
