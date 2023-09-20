from datetime import datetime
import json
import os
import random
import time
from typing import Any, Optional
import pytest
import dotenv
from os.path import dirname, abspath, join, isfile
from src import custom_types, utils, procedures

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
def sample_config() -> Any:
    """use the config template as a temporary config file"""
    CONFIG_FILE = join(PROJECT_DIR, "config", "config.json")
    TMP_CONFIG_FILE = join(PROJECT_DIR, "config", "config.tmp.json")

    with open(join(PROJECT_DIR, "config", "config.template.json")) as f:
        sample_config = custom_types.Config(**json.load(f))

    _save_file(
        CONFIG_FILE,
        TMP_CONFIG_FILE,
        json.dumps(sample_config.dict(), indent=4),
    )

    yield sample_config

    _restore_file(CONFIG_FILE, TMP_CONFIG_FILE)


@pytest.fixture(scope="function")
def log_files() -> Any:
    """
    1. store actual log files in a temporary location
    2. set up a new, empty log file just for the test
    3. restore the original log file after the test
    """

    LOG_FILE = join(
        PROJECT_DIR, "logs", "archive", datetime.now().strftime("%Y-%m-%d.log")
    )
    TMP_LOG_FILE = join(
        PROJECT_DIR, "logs", "archive", datetime.now().strftime("%Y-%m-%d.tmp.log")
    )

    _save_file(LOG_FILE, TMP_LOG_FILE, "")

    yield

    _restore_file(LOG_FILE, TMP_LOG_FILE)

    with open(TMP_LOG_FILE) as f:
        logs_after_test = f.read()
    print("*** LOGS AFTER TEST:")
    print(logs_after_test, end="")
    print("***")


"""
@pytest.fixture(scope="function")
def empty_active_mqtt_queue() -> Any:
    start and stop the background processing of messages

    active_mqtt_queue = utils.ActiveMQTTQueue()
    active_mqtt_queue.remove_messages_by_status("pending")
    active_mqtt_queue.remove_messages_by_status("in-progress")
    active_mqtt_queue.remove_messages_by_status("done")

    yield

"""


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
def messaging_agent_with_sending(
    log_files: None,
    mqtt_client_environment: None,
    mqtt_data_files: None,
    sample_config: None,
) -> Any:
    """start and stop the background processing of messages"""

    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = True

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    yield

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()


@pytest.fixture(scope="function")
def messaging_agent_without_sending(
    log_files: None,
    mqtt_client_environment: None,
    mqtt_data_files: None,
    sample_config: None,
) -> Any:
    """start and stop the background processing of messages"""

    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = False

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    yield

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()
