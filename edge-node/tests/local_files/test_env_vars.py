import pytest
import os
from os.path import dirname
import dotenv
from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


@pytest.mark.remote_update
@pytest.mark.version_update
def test_env_vars() -> None:
    """checks whether the local config/.env can be loaded"""

    env_file_path = os.path.join(PROJECT_DIR, "config", ".env")
    assert os.path.isfile(env_file_path), f"{env_file_path} is not a file"

    dotenv.load_dotenv(env_file_path)
    custom_types.MQTTConfig(
        station_identifier=os.environ.get("HERMES_MQTT_IDENTIFIER"),
        mqtt_url=os.environ.get("HERMES_MQTT_URL"),
        mqtt_port=os.environ.get("HERMES_MQTT_PORT"),
        mqtt_username=os.environ.get("HERMES_MQTT_USERNAME"),
        mqtt_password=os.environ.get("HERMES_MQTT_PASSWORD"),
        mqtt_base_topic=os.environ.get("HERMES_MQTT_BASE_TOPIC"),
    )
