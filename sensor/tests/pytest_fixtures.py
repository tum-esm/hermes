from datetime import datetime
import os
import random
import time
from typing import Any, Generator, Optional
import pytest
import dotenv
import sys
from os.path import dirname, abspath, join, isfile

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils


def _save_file(
    original_path: str, temporary_path: str, test_content: Optional[str]
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


@pytest.fixture
def mqtt_client_environment() -> Generator[None, None, None]:
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

    utils.mqtt_connection.MQTTConnection.deinit()


@pytest.fixture
def mqtt_data_files() -> Any:
    """start and stop the background sending loop of the SendingMQTTClient"""

    ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "active-mqtt-messages.db")
    TMP_ACTIVE_MESSAGES_FILE = join(PROJECT_DIR, "data", "active-mqtt-messages.tmp.db")

    TEST_MESSAGE_DATE_STRING = datetime.utcnow().strftime("%Y-%m-%d")
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

    yield

    _restore_file(ACTIVE_MESSAGES_FILE, TMP_ACTIVE_MESSAGES_FILE)
    _restore_file(MESSAGE_ARCHIVE_FILE, TMP_MESSAGE_ARCHIVE_FILE)


@pytest.fixture
def mqtt_sending_loop(mqtt_client_environment: None) -> Any:
    """start and stop the background sending loop of the SendingMQTTClient"""

    utils.SendingMQTTClient.init_sending_loop_process()

    yield

    utils.SendingMQTTClient.deinit_sending_loop_process()


@pytest.fixture
def mqtt_archiving_loop(mqtt_client_environment: None) -> Any:
    """start and stop the background sending loop of the SendingMQTTClient"""

    utils.SendingMQTTClient.init_archiving_loop_process()

    yield

    utils.SendingMQTTClient.deinit_archiving_loop_process()


@pytest.fixture
def log_files() -> Any:
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


@pytest.fixture
def sample_config() -> Any:
    """use the config template as a temporary config file"""
    CONFIG_FILE = join(PROJECT_DIR, "config", "config.json")
    TMP_CONFIG_FILE = join(PROJECT_DIR, "config", "config.tmp.json")

    with open(join(PROJECT_DIR, "config", "config.template.json")) as f:
        sample_config = f.read()
    _save_file(CONFIG_FILE, TMP_CONFIG_FILE, sample_config)

    yield

    _restore_file(CONFIG_FILE, TMP_CONFIG_FILE)
