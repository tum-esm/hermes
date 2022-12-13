from datetime import datetime
import json
import time
import pytest
from os.path import dirname, abspath, join
import sys
import deepdiff

from ..pytest_fixtures import mqtt_client_environment, mqtt_sending_loop, log_files
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import interfaces, custom_types

ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
MESSAGE_ARCHIVE_FILE = join(
    PROJECT_DIR,
    "data",
    "archive",
    f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
)


@pytest.mark.integration
def test_mqtt_sending(mqtt_sending_loop: None, log_files: None) -> None:
    interfaces.SendingMQTTClient.check_errors()
    with open(ACTIVE_MESSAGES_FILE, "r") as f:
        active_mqtt_message_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
    assert active_mqtt_message_queue.max_identifier == 0
    assert len(active_mqtt_message_queue.messages) == 0

    config = custom_types.Config(
        **{
            "version": "0.1.0",
            "revision": 17,
            "general": {"station_name": "pytest-dummy-config"},
            "valves": {
                "air_inlets": [
                    {"number": 1, "direction": 300},
                    {"number": 2, "direction": 50},
                ]
            },
        }
    )

    # enqueue dummy message
    dummy_measurement_message = custom_types.MQTTMeasurementMessageBody(
        timestamp=datetime.now().timestamp(),
        value=custom_types.CO2SensorData(raw=0.0, compensated=0.0, filtered=0.0),
    )
    interfaces.SendingMQTTClient.enqueue_message(
        config,
        dummy_measurement_message,
    )

    # assert dummy message to be in active queue
    with open(ACTIVE_MESSAGES_FILE, "r") as f:
        active_mqtt_message_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
    assert active_mqtt_message_queue.max_identifier == 1
    assert len(active_mqtt_message_queue.messages) == 1
    assert active_mqtt_message_queue.messages[0].header.identifier == 1
    assert active_mqtt_message_queue.messages[0].header.status == "pending"
    assert active_mqtt_message_queue.messages[0].header.revision == config.revision
    assert (
        deepdiff.DeepDiff(
            active_mqtt_message_queue.messages[0].body.dict(),
            dummy_measurement_message.dict(),
        )
        == {}
    )

    def empty_active_queue() -> bool:
        with open(ACTIVE_MESSAGES_FILE, "r") as f:
            active_mqtt_message_queue = custom_types.ActiveMQTTMessageQueue(
                **json.load(f)
            )
        return (
            len(active_mqtt_message_queue.messages) == 0
            and active_mqtt_message_queue.max_identifier == 1
        )

    # assert active queue to be empty
    wait_for_condition(
        is_successful=empty_active_queue,
        timeout_seconds=20,
        timeout_message="active queue is not empty after 20 second timeout",
    )

    # assert dummy message to be in archive
    with open(MESSAGE_ARCHIVE_FILE, "r") as f:
        archived_mqtt_messages = custom_types.ArchivedMQTTMessageQueue(
            messages=json.load(f)
        ).messages
    assert len(archived_mqtt_messages) == 1
    assert archived_mqtt_messages[0].header.identifier == 1
    assert archived_mqtt_messages[0].header.status == "delivered"
    assert (
        deepdiff.DeepDiff(
            archived_mqtt_messages[0].body.dict(),
            dummy_measurement_message.dict(),
        )
        == {}
    )

    # assert that sending loop is still functioning correctly
    interfaces.SendingMQTTClient.check_errors()
