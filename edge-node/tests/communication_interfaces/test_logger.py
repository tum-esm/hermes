from datetime import datetime
import json
import os
import time
import pytest
from ..pytest_utils import expect_log_file_contents, wait_for_condition
from os.path import dirname, abspath, join
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, custom_types

@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_logger_without_sending(messaging_agent_without_sending: None) -> None:
    _test_logger(mqtt_communication_enabled=False)


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_logger_with_sending(messaging_agent_with_sending: None) -> None:
    _test_logger(mqtt_communication_enabled=True)


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
def test_very_long_exception_cutting(messaging_agent_with_sending: None) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = True
    message_queue = utils.MessageQueue()

    logger = utils.Logger(origin="pytests")

    message = utils.get_random_string(length=300)
    details = "\n".join(
        [utils.get_random_string(length=80) for i in range(250)]
    )  # 20.249 characters long

    expected_log_file_content = (
        f"pytests                 - ERROR         - {message}\n"
        + "--- details: -----------------\n"
        + f"{details}\n"
        + "------------------------------\n"
    )
    expected_mqtt_message = (
        f"pytests - {message[: (256 - 31)]} ... CUT (310 -> 256)"
        + " "
        + f"{details[: (16384 - 25)]} ... CUT (20249 -> 16384)"
    )

    assert len(message_queue.get_rows_by_status("pending")) == 0
    expect_log_file_contents(forbidden_content_blocks=[expected_log_file_content])

    logger.error(message=message, config=config, details=details)

    mqtt_messages = message_queue.get_rows_by_status("pending")
    assert len(mqtt_messages) == 1
    mqtt_message_content = mqtt_messages[0].content
    assert isinstance(mqtt_message_content, custom_types.MQTTLogMessage)
    assert mqtt_message_content.body.message == expected_mqtt_message
    expect_log_file_contents(required_content_blocks=[expected_log_file_content])

    wait_for_condition(
        lambda: len(message_queue.get_rows_by_status("pending")) == 0,
        timeout_message="message was not sent",
        timeout_seconds=10,
    )


def _test_logger(mqtt_communication_enabled: bool) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = mqtt_communication_enabled

    message_queue = utils.MessageQueue()

    generated_log_lines = [
        "pytests                 - DEBUG         - some message a",
        "pytests                 - INFO          - some message b",
        "pytests                 - WARNING       - some message c",
        "pytests                 - ERROR         - some message d",
        "pytests                 - EXCEPTION     - ZeroDivisionError: division by zero",
        "pytests                 - EXCEPTION     - customlabel, ZeroDivisionError: division by zero",
    ]

    expect_log_file_contents(forbidden_content_blocks=generated_log_lines)
    assert len(
        [
            m
            for m in (
                message_queue.get_rows_by_status("in-progress")
                + message_queue.get_rows_by_status("pending")
            )
        ]
    ) == (1 if mqtt_communication_enabled else 0)

    TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
    MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
    )
    EXPECTED_MQTT_TOPIC = (
        (
            os.environ["HERMES_MQTT_BASE_TOPIC"]
            + "log-messages/"
            + os.environ["HERMES_MQTT_IDENTIFIER"]
        )
        if mqtt_communication_enabled
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
        logger.exception(e, label="customlabel", config=config)

    expect_log_file_contents(required_content_blocks=generated_log_lines)

    # -------------------------------------------------------------------------
    # check whether all records are correctly inserted in sending queue

    active_logs_messages = [
        custom_types.MQTTLogMessage(**m.content.dict())
        for m in (
            message_queue.get_rows_by_status("pending")
            if mqtt_communication_enabled
            else []
        )
    ]
    active_logs_messages.sort(key=lambda m: m.body.timestamp)
    assert len(active_logs_messages) == (4 if mqtt_communication_enabled else 0)

    if mqtt_communication_enabled:
        assert active_logs_messages[0].header.mqtt_topic == None
        assert active_logs_messages[0].body.severity == "warning"
        assert active_logs_messages[0].body.message == "pytests - some message c "

        assert active_logs_messages[1].header.mqtt_topic == None
        assert active_logs_messages[1].body.severity == "error"
        assert active_logs_messages[1].body.message == "pytests - some message d "

        assert active_logs_messages[2].header.mqtt_topic == None
        assert active_logs_messages[2].body.severity == "error"

        # -------------------------------------------------------------------------
        # wait until sending queue is empty

        def empty_pending_queue() -> bool:
            return (
                len(message_queue.get_rows_by_status("pending"))
                + len(message_queue.get_rows_by_status("in-progress"))
            ) == 0

        wait_for_condition(
            empty_pending_queue,
            timeout_seconds=12,
            timeout_message="active queue is not empty after 12 second timeout",
        )

        time.sleep(2)

    # -------------------------------------------------------------------------
    # check whether archive contains correct messages

    archived_log_messages = []

    with open(MESSAGE_ARCHIVE_FILE, "r") as f:
        for message in [json.loads(m) for m in f.read().split("\n") if len(m) > 0]:
            try:
                archived_log_messages.append(custom_types.MQTTLogMessage(**message))
            except:
                pass
    archived_log_messages.sort(key=lambda m: m.body.timestamp)
    assert len(archived_log_messages) == 4
    assert archived_log_messages[0].header.mqtt_topic == None
    assert archived_log_messages[0].body.severity == "warning"
    assert archived_log_messages[0].body.message == "pytests - some message c "

    assert archived_log_messages[1].header.mqtt_topic == None
    assert archived_log_messages[1].body.severity == "error"
    assert archived_log_messages[1].body.message == "pytests - some message d "

    assert archived_log_messages[2].header.mqtt_topic == None
    assert archived_log_messages[2].body.severity == "error"
