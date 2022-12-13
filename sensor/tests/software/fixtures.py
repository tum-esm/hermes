import os
import time
import pytest
import dotenv
import sys
from os.path import dirname, abspath, join

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)
from src import utils


@pytest.fixture(scope="session")
def mqtt_client_environment():
    MQTT_ENV_VARS_PATH = join(PROJECT_DIR, "config", ".env.testing")
    dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

    test_station_identifier = f"test-station-identifier-{round(time.time())}"
    test_base_topic = f"/development/{round(time.time())*2}"
    os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"] = test_station_identifier
    os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"] = test_base_topic

    yield

    utils.mqtt.MQTTClient.deinit()


def save_file(original_path: str, temporary_path: str, test_content: str) -> None:
    assert not os.path.exists(temporary_path)

    try:
        os.rename(original_path, temporary_path)
    except FileNotFoundError:
        pass

    with open(original_path, "w") as f:
        f.write(test_content)


def restore_file(original_path: str, temporary_path: str):
    os.remove(original_path)
    try:
        os.rename(temporary_path, original_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def log_files():
    LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
    TMP_LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.tmp.log")

    save_file(LOG_FILE, TMP_LOG_FILE, "")

    yield

    restore_file(LOG_FILE, TMP_LOG_FILE)
