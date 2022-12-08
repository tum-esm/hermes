import os
import time
import pytest
import dotenv
from os.path import dirname, abspath, join

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
MQTT_ENV_VARS_PATH = join(PROJECT_DIR, "config", ".env.testing")


@pytest.fixture(scope="session")
def mqtt_client_environment():
    dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

    test_station_identifier = f"test-station-identifier-{round(time.time())}"
    test_base_topic = f"/development/{round(time.time())*2}"
    os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"] = test_station_identifier
    os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"] = test_base_topic

    yield
