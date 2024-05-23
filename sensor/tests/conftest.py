import os
import dotenv
from typing import Any
import random
import pytest
import time
from os.path import dirname, abspath, join

PROJECT_DIR = dirname(dirname(abspath(__file__)))


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
