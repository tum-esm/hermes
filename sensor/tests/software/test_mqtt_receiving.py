import json
import time
import pytest
from os.path import dirname, abspath, join
import sys

from ..pytest_fixtures import mqtt_client_environment, log_files
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import utils, hardware_interfaces


@pytest.mark.ci
def test_mqtt_receiving(mqtt_client_environment: None, log_files: None) -> None:
    mqtt_client = utils.mqtt_connection.MQTTConnection.get_client()
    mqtt_config = utils.mqtt_connection.MQTTConnection.get_config()

    config_topic = (
        f"{mqtt_config.mqtt_base_topic}/configuration/{mqtt_config.station_identifier}"
    )
    message = {"hello": f"you {round(time.time())/32}"}
    print(f"config_topic = {config_topic}")

    expect_log_lines(
        forbidden_lines=[
            f"mqtt-receiving-client - INFO - subscribing to topic {config_topic}",
        ]
    )

    receiving_client = utils.ReceivingMQTTClient()
    assert len(receiving_client.get_messages()) == 0
    time.sleep(1)

    expect_log_lines(
        required_lines=[
            f"mqtt-receiving-client - INFO - subscribing to topic {config_topic}",
        ]
    )

    message_info = mqtt_client.publish(
        topic=config_topic, payload=json.dumps(message), qos=1
    )
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )

    expect_log_lines(
        required_lines=[
            f"mqtt-receiving-loop - DEBUG - received message: ",
        ]
    )

    messages = receiving_client.get_messages()
    print(f"mesages = {messages}")
    assert messages == [{"topic": config_topic, "payload": message}]
