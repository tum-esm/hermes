from datetime import datetime
import json
import pytest
from os.path import dirname, abspath, join
import sys
import deepdiff

from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_data_files,
    messaging_agent_with_sending,
    messaging_agent_without_sending,
    log_files,
    sample_config,
)
from ..pytest_utils import wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
CONFIG_TEMPLATE_PATH = join(PROJECT_DIR, "config", "config.template.json")
sys.path.append(PROJECT_DIR)

from src import utils, custom_types

ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
TEST_MESSAGE_DATE_STRING = datetime.utcnow().strftime("%Y-%m-%d")
MESSAGE_ARCHIVE_FILE = join(
    PROJECT_DIR,
    "data",
    "archive",
    f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
)


@pytest.mark.config_update
@pytest.mark.ci
def test_messaging_without_sending(messaging_agent_without_sending: None) -> None:
    _test_messaging(mqtt_communication_enabled=False)


@pytest.mark.ci
def test_messaging_with_sending(messaging_agent_with_sending: None) -> None:
    _test_messaging(mqtt_communication_enabled=True)


def _test_messaging(mqtt_communication_enabled: bool) -> None:
    active_mqtt_queue = utils.ActiveMQTTQueue()

    assert len(active_mqtt_queue.get_rows_by_status("pending")) == 0
    assert len(active_mqtt_queue.get_rows_by_status("in-progress")) == 0
    assert len(active_mqtt_queue.get_rows_by_status("done")) == 0

    with open(CONFIG_TEMPLATE_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.active_components.mqtt_communication = mqtt_communication_enabled

    # enqueue dummy message
    dummy_data_message_body = custom_types.MQTTDataMessageBody(
        revision=config.revision,
        timestamp=datetime.utcnow().timestamp(),
        value=custom_types.MQTTCO2Data(
            variant="co2",
            data=custom_types.CO2SensorData(
                raw=0.0,
                compensated=0.0,
                filtered=0.0,
            ),
        ),
    )
    active_mqtt_queue.enqueue_message(config, dummy_data_message_body)

    # assert dummy message to be in active queue
    records = active_mqtt_queue.get_rows_by_status(
        "pending" if mqtt_communication_enabled else "done"
    )
    assert len(records) == 1
    record = records[0]
    differences = deepdiff.DeepDiff(
        record.content.body.dict(),
        dummy_data_message_body.dict(),
    )
    print(f"differences = {differences}")
    assert differences == {}

    def empty_active_queue() -> bool:
        return (
            len(active_mqtt_queue.get_rows_by_status("pending"))
            + len(active_mqtt_queue.get_rows_by_status("in-progress"))
            + len(active_mqtt_queue.get_rows_by_status("done"))
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
    assert len(archived_mqtt_messages) == 1
    stored_data_message = custom_types.MQTTDataMessage(**archived_mqtt_messages[0])
    assert (
        deepdiff.DeepDiff(
            stored_data_message.body.dict(),
            dummy_data_message_body.dict(),
        )
        == {}
    )
