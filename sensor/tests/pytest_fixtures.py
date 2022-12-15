from datetime import datetime
import os
import time
from typing import Generator
import pytest
import dotenv
import sys
from os.path import dirname, abspath, join, isfile

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware_interfaces


def _save_file(
    original_path: str, temporary_path: str, test_content: str | None
) -> None:
    if isfile(temporary_path):
        os.remove(temporary_path)

    try:
        os.rename(original_path, temporary_path)
    except FileNotFoundError:
        pass

    if test_content is not None:
        with open(original_path, "w") as f:
            f.write(test_content)


def _restore_file(original_path: str, temporary_path: str) -> None:
    tmp_content = None
    if isfile(original_path):
        with open(original_path, "r") as f:
            tmp_content = f.read()
        os.remove(original_path)

    try:
        os.rename(temporary_path, original_path)
    except FileNotFoundError:
        pass

    if tmp_content is not None:
        with open(temporary_path, "w") as f:
            f.write(tmp_content)


@pytest.fixture(scope="session")
def mqtt_client_environment() -> Generator[None, None, None]:
    """load the environment variables from config/.env.testing
    and generate a dummy base-topic path"""

    MQTT_ENV_VARS_PATH = join(PROJECT_DIR, "config", ".env.testing")
    dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

    test_station_identifier = f"test-station-identifier-{round(time.time())}"
    test_base_topic = f"/development/{round(time.time())*2}"
    os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"] = test_station_identifier
    os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"] = test_base_topic

    yield

    utils.mqtt_connection.MQTTConnection.deinit()


@pytest.fixture(scope="session")
def mqtt_sending_loop(mqtt_client_environment: None) -> Generator[None, None, None]:
    """start and stop the background sending loop of the SendingMQTTClient"""

    ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
    TMP_ACTIVE_MESSAGES_FILE = join(
        PROJECT_DIR, "data", "incomplete-mqtt-messages.tmp.json"
    )

    TEST_MESSAGE_DATE_STRING = datetime.now().strftime("%Y-%m-%d")
    MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.json",
    )
    TMP_MESSAGE_ARCHIVE_FILE = join(
        PROJECT_DIR,
        "data",
        "archive",
        f"delivered-mqtt-messages-{TEST_MESSAGE_DATE_STRING}.tmp.json",
    )

    _save_file(ACTIVE_MESSAGES_FILE, TMP_ACTIVE_MESSAGES_FILE, None)
    _save_file(MESSAGE_ARCHIVE_FILE, TMP_MESSAGE_ARCHIVE_FILE, None)
    utils.SendingMQTTClient.init_sending_loop_process()

    yield

    utils.SendingMQTTClient.deinit_sending_loop_process()
    _restore_file(ACTIVE_MESSAGES_FILE, TMP_ACTIVE_MESSAGES_FILE)
    _restore_file(MESSAGE_ARCHIVE_FILE, TMP_MESSAGE_ARCHIVE_FILE)


@pytest.fixture
def log_files() -> Generator[None, None, None]:
    """
    1. store actual log files in a temporary location
    2. set up a new, empty log file just for the test
    3. restore the original log file after the test
    """
    LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
    TMP_LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.tmp.log")

    _save_file(LOG_FILE, TMP_LOG_FILE, "")

    yield

    _restore_file(LOG_FILE, TMP_LOG_FILE)
