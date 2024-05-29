from datetime import datetime
import json
import pytest
from os.path import dirname, abspath, join
import sys
import deepdiff
from ..pytest_utils import wait_for_condition
import time

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
CONFIG_PATH = join(PROJECT_DIR, "config", "config.json")
sys.path.append(PROJECT_DIR)

from src import utils, custom_types

ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
MESSAGE_ARCHIVE_FILE = join(
    PROJECT_DIR,
    "data",
    "archive",
    f"mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
)


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_message_sending_without_sending(messaging_agent_without_sending: None) -> None:
    _test_message_sending(mqtt_communication_enabled=False)


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_message_sending_with_sending(messaging_agent_with_sending: None) -> None:
    _test_message_sending(mqtt_communication_enabled=True)


def _test_message_sending(mqtt_communication_enabled: bool) -> None:
    message_queue = utils.MessageQueue()

    assert len(
        [
            m
            for m in (
                message_queue.get_rows_by_status("in-progress")
                + message_queue.get_rows_by_status("pending")
            )
        ]
    ) == (1 if mqtt_communication_enabled else 0)

    with open(CONFIG_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.active_components.send_messages_over_mqtt = mqtt_communication_enabled

    # enqueue dummy message
    dummy_data_message_body = custom_types.MQTTMeasurementMessageBody(
                    revision=1,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTMeasurementData(
                        gmp343_raw=0.0,
                        gmp343_compensated=0.0,
                        gmp343_filtered=0.0,
                        bme280_temperature=0.0,
                        bme280_humidity=0.0,
                        bme280_pressure=0.0,
                        sht45_temperature=0.0,
                        sht45_humidity=0.0,
                        gmp343_temperature=0.0,
                    )
                )
    
    message_queue.enqueue_message(
                config,
                dummy_data_message_body
            )

    # assert dummy message to be in active queue
    records = (
        message_queue.get_rows_by_status("pending")
        if mqtt_communication_enabled
        else []
    )
    assert len(records) == (1 if mqtt_communication_enabled else 0)

    if mqtt_communication_enabled:
        record = records[0]
        differences = deepdiff.DeepDiff(
            record.content.body.dict(),
            dummy_data_message_body.dict(),
        )
        print(f"differences = {differences}")
        assert differences == {}

        def empty_active_queue() -> bool:
            return (
                len(message_queue.get_rows_by_status("pending"))
                + len(message_queue.get_rows_by_status("in-progress"))
            ) == 0

        # assert active queue to be empty
        wait_for_condition(
            is_successful=empty_active_queue,
            timeout_seconds=12,
            timeout_message="active queue is not empty after 12 second timeout",
        )

    # assert dummy message to be in archive
    with open(MESSAGE_ARCHIVE_FILE, "r") as f:
        archived_mqtt_messages = [json.loads(m) for m in f.read().split("\n")[:-1]]
    assert len(archived_mqtt_messages) == (2 if mqtt_communication_enabled else 1)
    stored_message = custom_types.MQTTMeasurementMessage(
        **archived_mqtt_messages[1 if mqtt_communication_enabled else 0]
    )
    assert (
        deepdiff.DeepDiff(
            stored_message.body.dict(),
            dummy_data_message_body.dict(),
        )
        == {}
    )
