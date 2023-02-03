import json
import time
import pytest
from os.path import dirname, abspath, join
import sys
import deepdiff

from ..pytest_fixtures import mqtt_client_environment, log_files
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import custom_types, utils


@pytest.mark.config_update
@pytest.mark.ci
def test_mqtt_receiving(mqtt_client_environment: None, log_files: None) -> None:
    mqtt_client = utils.mqtt_connection.MQTTConnection.get_client()
    mqtt_config = utils.mqtt_connection.MQTTConnection.get_config()

    config_topic = (
        f"{mqtt_config.mqtt_base_topic}configurations/{mqtt_config.station_identifier}"
    )
    message = custom_types.MQTTConfigurationRequest(
        revision=1, configuration={"version": "0.1.0", "other_params": 30}
    ).dict()
    print(f"config_topic = {config_topic}")

    expect_log_lines(
        forbidden_lines=[
            f"mqtt-receiving-client   - INFO          - subscribing to topic {config_topic}",
        ]
    )

    receiving_client = utils.ReceivingMQTTClient()
    assert receiving_client.get_config_message() is None
    time.sleep(1)

    expect_log_lines(
        required_lines=[
            f"mqtt-receiving-client   - INFO          - subscribing to topic {config_topic}",
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
            f"mqtt-receiving-loop     - DEBUG         - received message: ",
        ]
    )

    new_config_message = receiving_client.get_config_message()
    assert new_config_message is not None

    differences = deepdiff.DeepDiff(new_config_message.dict(), message)
    print(f"differences = {differences}")
    assert differences == {}
