from datetime import datetime
import json
import os
import pytest

from ..pytest_utils import expect_log_lines, wait_for_condition
from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_sending_loop,
    mqtt_archiving_loop,
    mqtt_data_files,
    log_files,
    sample_config,
)
from os.path import dirname, abspath, join
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
CONFIG_PATH = join(PROJECT_DIR, "config", "config.json")
ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
sys.path.append(PROJECT_DIR)

from src import utils, custom_types

# TODO: make the message queue assertions prettier


@pytest.mark.config_update
@pytest.mark.ci
def test_logger_without_sending(
    mqtt_data_files: None,
    mqtt_archiving_loop: None,
    log_files: None,
    sample_config: None,
) -> None:
    _test_logger(sending_enabled=False)


@pytest.mark.ci
def test_logger_with_sending(
    mqtt_data_files: None,
    mqtt_archiving_loop: None,
    mqtt_sending_loop: None,
    log_files: None,
    sample_config: None,
) -> None:
    _test_logger(sending_enabled=True)


def _test_logger(sending_enabled: bool) -> None:
    utils.SendingMQTTClient.check_errors()

    with open(CONFIG_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.revision = 17
        config.active_components.mqtt_data_sending = sending_enabled

    active_mqtt_queue = utils.ActiveMQTTQueue()

    generated_log_lines = [
        "pytests                 - DEBUG         - some message a",
        "pytests                 - INFO          - some message b",
        "pytests                 - WARNING       - some message c",
        "pytests                 - ERROR         - some message d",
        "pytests                 - EXCEPTION     - ZeroDivisionError occured",
    ]

    expect_log_lines(forbidden_lines=generated_log_lines)
    assert len(active_mqtt_queue.get_rows_by_status("pending")) == 0
    assert len(active_mqtt_queue.get_rows_by_status("in-progress")) == 0
    assert len(active_mqtt_queue.get_rows_by_status("done")) == 0

    TEST_MESSAGE_DATE_STRING = datetime.utcnow().strftime("%Y-%m-%d")
    MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
    )
    EXPECTED_MQTT_TOPIC = (
        (os.environ["HERMES_MQTT_BASE_TOPIC"] + "statuses/" + utils.get_hostname())
        if sending_enabled
        else None
    )

    # -------------------------------------------------------------------------
    # check whether logs lines were written correctly

    logger = utils.Logger(origin="pytests")
    logger.debug("some message a")
    logger.info("some message b")
    logger.warning("some message c", config=config)
    logger.error("some message d", config=config)
    try:
        30 / 0
    except Exception as e:
        logger.exception(e, config=config)

    expect_log_lines(required_lines=generated_log_lines)

    # -------------------------------------------------------------------------
    # check whether all records are correctly inserted in sending queue

    active_status_messages = [
        custom_types.MQTTStatusMessage(**m.content.dict())
        for m in active_mqtt_queue.get_rows_by_status(
            "pending" if sending_enabled else "done"
        )
    ]
    active_status_messages.sort(key=lambda m: m.body.timestamp)
    assert len(active_status_messages) == 3
    assert all([m.variant == "status" for m in active_status_messages])

    assert active_status_messages[0].header.mqtt_topic == None
    assert active_status_messages[0].body.severity == "warning"
    assert active_status_messages[0].body.subject == "pytests - some message c"

    assert active_status_messages[1].header.mqtt_topic == None
    assert active_status_messages[1].body.severity == "error"
    assert active_status_messages[1].body.subject == "pytests - some message d"

    assert active_status_messages[2].header.mqtt_topic == None
    assert active_status_messages[2].body.severity == "error"
    assert active_status_messages[2].body.subject == "pytests - ZeroDivisionError"

    # -------------------------------------------------------------------------
    # wait until sendin queue is empty

    def empty_pending_queue() -> bool:
        return (
            len(active_mqtt_queue.get_rows_by_status("pending"))
            + len(active_mqtt_queue.get_rows_by_status("in-progress"))
            + len(active_mqtt_queue.get_rows_by_status("done"))
        ) == 0

    wait_for_condition(
        empty_pending_queue,
        timeout_seconds=12,
        timeout_message="active queue is not empty after 12 second timeout",
    )

    # -------------------------------------------------------------------------
    # check whether archive contains correct messages

    with open(MESSAGE_ARCHIVE_FILE, "r") as f:
        archived_data_messages = [
            custom_types.MQTTStatusMessage(**m)
            for m in [json.loads(m) for m in f.read().split("\n") if len(m) > 0]
        ]
    archived_data_messages.sort(key=lambda m: m.body.timestamp)
    assert len(archived_data_messages) == 3
    assert archived_data_messages[0].header.mqtt_topic == EXPECTED_MQTT_TOPIC
    assert archived_data_messages[0].body.severity == "warning"
    assert archived_data_messages[0].body.subject == "pytests - some message c"

    assert archived_data_messages[1].header.mqtt_topic == EXPECTED_MQTT_TOPIC
    assert archived_data_messages[1].body.severity == "error"
    assert archived_data_messages[1].body.subject == "pytests - some message d"

    assert archived_data_messages[2].header.mqtt_topic == EXPECTED_MQTT_TOPIC
    assert archived_data_messages[2].body.severity == "error"
    assert archived_data_messages[2].body.subject == "pytests - ZeroDivisionError"

    utils.SendingMQTTClient.check_errors()
