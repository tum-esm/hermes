import os
from datetime import datetime
import dotenv
from typing import Any, Optional
import random
import pytest
import time
from os.path import dirname, abspath, join, isfile
from src import utils, procedures

PROJECT_DIR = dirname(dirname(abspath(__file__)))


def _save_file(
    original_path: str, temporary_path: str, test_content: Optional[str]
) -> None:
    if isfile(temporary_path):
        os.remove(temporary_path)

    try:
        os.rename(original_path, temporary_path)
    except FileNotFoundError:
        pass

    if test_content is None:
        if isfile(original_path):
            os.remove(original_path)
    else:
        with open(original_path, "w") as f:
            f.write(test_content)


def _restore_file(original_path: str, temporary_path: str) -> None:
    tmp_content = None
    if isfile(original_path):
        with open(original_path, "rb") as f:
            tmp_content = f.read()
        os.remove(original_path)

    try:
        os.rename(temporary_path, original_path)
    except FileNotFoundError:
        pass

    if tmp_content is not None:
        with open(temporary_path, "wb") as f:
            f.write(tmp_content)


@pytest.fixture(scope="function")
def mqtt_data_files() -> Any:
    """start and stop the background sending loop of the SendingMQTTClient"""
    print("clearing mqtt data files")

    ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "active-mqtt-messages.db")
    TMP_ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "active-mqtt-messages.tmp.db")

    TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
    MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
    )
    TMP_MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"mqtt-messages-{TEST_MESSAGE_DATE_STRING}.tmp.json",
    )

    _save_file(ACTIVE_MESSAGES_FILE, TMP_ACTIVE_MESSAGES_FILE, None)
    _save_file(MESSAGE_ARCHIVE_FILE, TMP_MESSAGE_ARCHIVE_FILE, None)

    yield

    _restore_file(ACTIVE_MESSAGES_FILE, TMP_ACTIVE_MESSAGES_FILE)
    _restore_file(MESSAGE_ARCHIVE_FILE, TMP_MESSAGE_ARCHIVE_FILE)


@pytest.fixture(scope="function")
def mqtt_client_environment() -> Any:
    """load the environment variables from config/.env.testing
    and generate a dummy base-topic path"""

    dotenv.load_dotenv(join(PROJECT_DIR, "config", ".env"))
    dotenv.load_dotenv(join(PROJECT_DIR, "config", ".env.testing"))

    timestamp = round(time.time())
    os.environ["HERMES_MQTT_IDENTIFIER"] = "".join(
        random.choices([chr(a) for a in range(ord("a"), ord("z") + 1)], k=20)
    )
    os.environ["HERMES_MQTT_BASE_TOPIC"] = f"development/test-{timestamp}/"

    yield


@pytest.fixture(scope="function")
def messaging_agent_with_sending() -> Any:
    """start and stop the background processing of messages"""

    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = True

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    yield

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()


@pytest.fixture(scope="function")
def messaging_agent_without_sending() -> Any:
    """start and stop the background processing of messages"""

    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = False

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    yield

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()
