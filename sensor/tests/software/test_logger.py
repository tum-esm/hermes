from datetime import datetime
import json
import os
import pytest

from ..pytest_utils import expect_log_lines, wait_for_condition
from ..pytest_fixtures import mqtt_client_environment, mqtt_sending_loop, log_files
from os.path import dirname, abspath, join
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
CONFIG_TEMPLATE_PATH = join(PROJECT_DIR, "config", "config.template.json")
ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
sys.path.append(PROJECT_DIR)

from src import utils, custom_types

# TODO: make the message queue assertions prettier


@pytest.mark.ci
def test_logger(mqtt_sending_loop: None, log_files: None) -> None:

    utils.SendingMQTTClient.init_archiving_loop_process()

    if not os.path.exists(ACTIVE_MESSAGES_FILE):
        with open(ACTIVE_MESSAGES_FILE, "w") as f:
            json.dump({"max_identifier": 0, "messages": []}, f)

    with open(CONFIG_TEMPLATE_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.revision = 17

    generated_log_lines = [
        "pytests - DEBUG - some message a",
        "pytests - INFO - some message b",
        "pytests - WARNING - some message c",
        "pytests - ERROR - some message d",
        "pytests - EXCEPTION - ZeroDivisionError occured",
    ]

    expect_log_lines(forbidden_lines=generated_log_lines)
    with open(ACTIVE_MESSAGES_FILE, "r") as f:
        active_message_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
    assert active_message_queue.max_identifier == 0
    assert len(active_message_queue.messages) == 0

    TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
    MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
    )

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

    with open(ACTIVE_MESSAGES_FILE, "r") as f:
        active_message_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
    assert active_message_queue.max_identifier == 3
    assert len(active_message_queue.messages) == 3
    assert any(
        [
            (
                m.header.identifier == 1
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "warning"
                and m.body.subject == "some message c"
            )
            for m in active_message_queue.messages
        ]
    )
    assert any(
        [
            (
                m.header.identifier == 2
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "error"
                and m.body.subject == "some message d"
            )
            for m in active_message_queue.messages
        ]
    )
    assert any(
        [
            (
                m.header.identifier == 3
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "error"
                and m.body.subject == "ZeroDivisionError"
            )
            for m in active_message_queue.messages
        ]
    )

    def empty_pending_queue() -> bool:
        with open(ACTIVE_MESSAGES_FILE, "r") as f:
            active_message_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
        return (active_message_queue.max_identifier == 3) and (
            len(active_message_queue.messages) == 0
        )

    wait_for_condition(
        empty_pending_queue, timeout_message="log messages were not sent over MQTT"
    )

    expected_message_topic = (
        os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"]
        + "statuses/"
        + os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"]
    )
    with open(MESSAGE_ARCHIVE_FILE, "r") as f:
        message_archive = custom_types.ArchivedMQTTMessageQueue(messages=json.load(f))
    assert len(message_archive.messages) == 3
    assert any(
        [
            (
                m.header.identifier == 1
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "warning"
                and m.body.subject == "some message c"
            )
            for m in message_archive.messages
        ]
    )
    assert any(
        [
            (
                m.header.identifier == 2
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "error"
                and m.body.subject == "some message d"
            )
            for m in message_archive.messages
        ]
    )
    assert any(
        [
            (
                m.header.identifier == 3
                and m.header.status == "sending-skipped"
                and m.header.mqtt_topic is None
                and m.variant == "status"
                and m.body.severity == "error"
                and m.body.subject == "ZeroDivisionError"
            )
            for m in message_archive.messages
        ]
    )
