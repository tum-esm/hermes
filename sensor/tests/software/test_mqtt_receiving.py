import json
import os
import time

import pytest
from fixtures import mqtt_client_environment, log_files
from os.path import dirname, abspath, join
import sys

from utils import expect_log_lines

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import utils, interfaces


@pytest.mark.ci
def test_mqtt_receiving(mqtt_client_environment, log_files) -> None:
    mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()
    config_topic = (
        f"{mqtt_config.mqtt_base_topic}/configuration/{mqtt_config.station_identifier}"
    )
    message = {"hello": "you"}

    expect_log_lines(
        forbidden_lines=[
            f"mqtt-receiving-client - INFO - subscribing to topic {config_topic}",
            "mqtt-receiving-client - INFO - starting receiving loop",
        ]
    )

    receiving_client = interfaces.ReceivingMQTTClient()
    assert len(receiving_client.get_messages()) == 0
    time.sleep(1)

    expect_log_lines(
        required_lines=[
            f"mqtt-receiving-client - INFO - subscribing to topic {config_topic}",
            "mqtt-receiving-client - INFO - starting receiving loop",
        ]
    )

    mqtt_client.publish(topic=config_topic, payload=json.dumps(message), qos=1)
    time.sleep(3)

    expect_log_lines(
        required_lines=[
            f"mqtt-receiving-loop - DEBUG - received message: ",
        ]
    )

    messages = receiving_client.get_messages()
    print(f"mesages = {json.dumps(messages, indent=4)}")
    assert messages == [{"topic": config_topic, "qos": 1, "payload": message}]
